import enum
import logging
from dataclasses import dataclass
from pathlib import Path

import click

from algokit.core.dispenser import (
    DISPENSER_ACCESS_TOKEN_KEY,
    DispenserApiAudiences,
    clear_dispenser_credentials,
    get_oauth_tokens,
    is_authenticated,
    process_dispenser_request,
    revoke_refresh_token,
    set_dispenser_credentials,
)
from algokit.core.utils import is_network_available

logger = logging.getLogger(__name__)


@dataclass
class DispenserAsset:
    asset_id: int
    decimals: int
    description: str


class OutputMode(enum.Enum):
    STDOUT = "stdout"
    FILE = "file"


class DispenserAssetName(enum.IntEnum):
    ALGO = 0


DISPENSER_ASSETS = {
    DispenserAssetName.ALGO: DispenserAsset(
        asset_id=0,
        decimals=6,
        description="Algo",
    ),
}

DEFAULT_CI_TOKEN_FILENAME = "algokit_ci_token.txt"

NOT_AUTHENTICATED_MESSAGE = "Please login first by running `algokit dispenser login` command"


def _handle_ci_token(output_mode: str, output_filename: str, token_data: dict) -> None:
    if output_mode == OutputMode.STDOUT.value:
        click.echo(f'\n{DISPENSER_ACCESS_TOKEN_KEY} (valid for 30 days):\n\n{token_data["access_token"]}\n')
        logger.warning(
            "Your CI access token has been printed to stdout.\n"
            "Please ensure you keep this token safe!\n"
            "If needed, clear your terminal history after copying the token!"
        )
    else:
        with Path.open(Path(output_filename), "w") as token_file:
            token_file.write(token_data["access_token"])
        logger.warning(
            f"Your CI access token has been saved to `{output_filename}`.\n"
            "Please ensure you keep this file safe or remove after copying the token!"
        )


class DispenserGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return_value = super().get_command(ctx, cmd_name)

        if return_value is None:
            return None
        elif is_network_available():
            return return_value
        else:
            logger.error("Please connect to internet first")
            raise click.exceptions.Exit(code=1)


@click.group("dispenser", cls=DispenserGroup)
def dispenser_group() -> None:
    """Interact with the AlgoKit TestNet Dispenser."""


@dispenser_group.command("logout", help="Logout of your Dispenser API account.")
def logout_command() -> None:
    if is_authenticated():
        try:
            revoke_refresh_token()
            clear_dispenser_credentials()
        except Exception as e:
            logger.debug(f"Error logging out {e}")
            raise click.ClickException("Error logging out") from e
        logger.info("Logout successful")
    else:
        logger.warning("Already logged out")


@dispenser_group.command("login", help="Login to your Dispenser API account.")
@click.option(
    "--ci", help="Generate an access token for CI. Issued for 30 days.", is_flag=True, default=False, required=False
)
@click.option(
    "--output",
    "-o",
    "output_mode",
    required=False,
    type=click.Choice([OutputMode.STDOUT.value, OutputMode.FILE.value], case_sensitive=False),
    default=OutputMode.STDOUT.value,
    help="Choose the output method for the access token. Defaults to `stdout`. Only applicable when --ci flag is set.",
)
@click.option(
    "--file",
    "-f",
    "output_filename",
    required=False,
    type=str,
    help=(
        "Output filename where you want to store the generated access token."
        f"Defaults to `{DEFAULT_CI_TOKEN_FILENAME}`. Only applicable when --ci flag is set and --output mode is `file`."
    ),
    default=DEFAULT_CI_TOKEN_FILENAME,
)
def login_command(*, ci: bool, output_mode: str, output_filename: str) -> None:
    if not ci and is_authenticated():
        logger.info("You are already logged in")
        return

    try:
        audience = DispenserApiAudiences.CI if ci else DispenserApiAudiences.USER
        custom_scopes = None if ci else "offline_access"
        token_data = get_oauth_tokens(api_audience=audience, custom_scopes=custom_scopes)

        if not token_data:
            raise click.ClickException("Error obtaining auth token")

        if ci:
            _handle_ci_token(output_mode, output_filename, token_data)
        else:
            set_dispenser_credentials(token_data)
            logger.info("Login successful")

    except Exception as e:
        raise click.ClickException(str(e)) from e


@dispenser_group.command("fund", help="Fund your wallet address with TestNet ALGOs.")
@click.option("--receiver", "-r", required=True, help="Receiver address to fund with TestNet ALGOs.")
@click.option("--amount", "-a", required=True, help="Amount to fund. Defaults to microAlgos.", default=1000000)
@click.option(
    "--whole-units",
    "whole_units",
    is_flag=True,
    help="Use whole units (Algos) instead of smallest divisible units (microAlgos). Disabled by default.",
    default=False,
)
def fund_command(*, receiver: str, amount: int, whole_units: bool) -> None:
    if not is_authenticated():
        logger.error(NOT_AUTHENTICATED_MESSAGE)
        return

    default_asset = DISPENSER_ASSETS[DispenserAssetName.ALGO]
    if whole_units:
        amount = amount * (10**default_asset.decimals)
        logger.debug(f"Converted algos to microAlgos: {amount}")

    try:
        response = process_dispenser_request(
            url_suffix=f"fund/{DISPENSER_ASSETS[DispenserAssetName.ALGO].asset_id}",
            data={"receiver": receiver, "amount": amount, "assetID": default_asset.asset_id},
            method="POST",
        )
    except Exception as e:
        logger.error(f"Error: {e}")
    else:
        response_body = response.json()
        processed_amount = (
            response_body["amount"] / (10**default_asset.decimals) if whole_units else response_body["amount"]
        )
        asset_description = default_asset.description if whole_units else f"μ{default_asset.description}"
        logger.info(
            f'Successfully funded {processed_amount} {asset_description}. Browse transaction at https://testnet.algoexplorer.io/tx/{response_body["txID"]}'
        )


@dispenser_group.command("refund", help="Refund ALGOs back to the dispenser wallet address.")
@click.option("--txID", "-t", "tx_id", required=True, help="Transaction ID of your refund operation.")
def refund_command(*, tx_id: str) -> None:
    if not is_authenticated():
        logger.error(NOT_AUTHENTICATED_MESSAGE)
        return

    try:
        process_dispenser_request(url_suffix="refund", data={"refundTransactionID": tx_id})
    except Exception as e:
        logger.error(f"Error: {e}")
    else:
        logger.info("Successfully processed refund transaction")


@dispenser_group.command("limit", help="Get information about current fund limit on your account. Resets daily.")
@click.option(
    "--whole-units",
    "whole_units",
    is_flag=True,
    help="Use whole units (Algos) instead of smallest divisible units (microAlgos). Disabled by default.",
    default=False,
)
def get_fund_limit(*, whole_units: bool) -> None:
    if not is_authenticated():
        logger.error(NOT_AUTHENTICATED_MESSAGE)
        return

    default_asset = DISPENSER_ASSETS[DispenserAssetName.ALGO]
    try:
        response = process_dispenser_request(url_suffix=f"fund/{default_asset.asset_id}/limit", data={}, method="GET")
    except Exception as e:
        logger.error(f"Error: {e}")
    else:
        response_amount = response.json()["amount"]
        processed_amount = response_amount / (10**default_asset.decimals) if whole_units else response_amount
        asset_description = default_asset.description if whole_units else f"μ{default_asset.description}"

        logger.info(f"Remaining daily fund limit: {processed_amount} {asset_description}")
