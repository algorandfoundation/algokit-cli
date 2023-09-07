import enum
import logging
from dataclasses import dataclass
from pathlib import Path

import click

from algokit.core.dispenser import (
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


assets = {
    DispenserAssetName.ALGO: DispenserAsset(
        asset_id=0,
        decimals=6,
        description="Algo",
    ),
}


def _handle_ci_token(output_mode: str, output_filename: str, token_data: dict) -> None:
    if output_mode == OutputMode.STDOUT.value:
        click.echo(f'\nAccess Token (valid for 30 days):\n\n{token_data["access_token"]}\n')
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
        logger.warning("Not logged in! To login, run `algokit dispenser login`")


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
    help="Choose the output method for the access token. Defaults to `stdout`. Only applicable when --ci flag is set",
)
@click.option(
    "--file",
    "-f",
    "output_filename",
    required=False,
    type=str,
    help=(
        "Output filename where you want to store the generated access token."
        "Defaults to `ci_token.txt`. Only applicable when --ci flag is set and --output mode is `file`."
    ),
    default="ci_token.txt",
)
def login_command(*, ci: bool, output_mode: str, output_filename: str) -> None:
    if not ci and is_authenticated():
        logger.info("Already logged in")
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
            logger.info("Logged in!")

    except Exception as e:
        logger.debug(str(e))
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
@click.option(
    "--ci",
    "ci",
    is_flag=True,
    default=False,
    help="Enable/disable interactions with Dispenser API via CI access token.",
)
def fund_command(*, receiver: str, amount: int, whole_units: bool, ci: bool) -> None:
    if not ci and not is_authenticated():
        logger.error("Please login first")
        return

    default_asset = assets[DispenserAssetName.ALGO]
    if whole_units:
        amount = amount * (10**default_asset.decimals)

    try:
        response = process_dispenser_request(
            url_suffix=f"fund/{assets[DispenserAssetName.ALGO].asset_id}",
            data={"receiver": receiver, "amount": amount, "assetID": default_asset.asset_id},
            ci=ci,
            method="POST",
        )
    except Exception as e:
        logger.debug("Error processing dispenser fund request: %s", e)
        raise click.ClickException(str(e)) from e

    if response:
        logger.info(response.json()["message"])


@dispenser_group.command("refund", help="Refund ALGOs back to the dispenser wallet address.")
@click.option("--txID", "-t", "tx_id", required=True, help="Transaction ID of your refund operation.")
@click.option(
    "--ci", is_flag=True, default=False, help="Enable/disable interactions with Dispenser API via CI access token."
)
def refund_command(*, tx_id: str, ci: bool) -> None:
    if not ci and not is_authenticated():
        logger.error("Please login first")
        return

    try:
        response = process_dispenser_request(url_suffix="refund", data={"refundTransactionID": tx_id}, ci=ci)
    except Exception as e:
        logger.debug("Error processing refund request: %s", e)
        raise click.ClickException(str(e)) from e

    if response:
        logger.info(response.json()["message"])


@dispenser_group.command("limit", help="Get information about current fund limit on your account. Resets daily.")
@click.option(
    "--whole-units",
    "whole_units",
    is_flag=True,
    help="Use whole units (Algos) instead of smallest divisible units (microAlgos). Disabled by default.",
    default=False,
)
@click.option(
    "--ci", is_flag=True, default=False, help="Enable/disable interactions with Dispenser API via CI access token."
)
def get_fund_limit(*, whole_units: bool, ci: bool) -> None:
    if not ci and not is_authenticated():
        logger.error("Please login first")
        return

    try:
        response = process_dispenser_request(
            url_suffix=f"fund/{assets[DispenserAssetName.ALGO].asset_id}/limit", data={}, ci=ci, method="GET"
        )
    except Exception as e:
        logger.debug("Error getting dispenser fund limit: %s", e)
        raise click.ClickException(str(e)) from e

    if response:
        response_amount = response.json()["amount"]
        amount = response_amount / (10 ** assets[DispenserAssetName.ALGO].decimals) if whole_units else response_amount
        logger.info(f"Remaining daily fund limit: {amount}")
