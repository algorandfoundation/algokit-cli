import logging
from pathlib import Path

import click
import keyring

from algokit.core.account import (
    KEYRING_KEY,
    KEYRING_NAMESPACE,
    DispenseApiAudiences,
    get_oauth_tokens,
    is_authenticated,
    process_dispenser_request,
    set_keyring_passwords,
)

logger = logging.getLogger(__name__)

assets = {
    "ALGO": {
        "asset_id": 0,
        "decimals": 6,
        "description": "Algorand token on Algorand TestNet",
    },
}


@click.group("account")
def account_group() -> None:
    """Account based commands"""


@account_group.command("dispense", help="Dispense funds to a wallet")
@click.option("--wallet", required=True, help="Wallet address to dispense to")
@click.option("--amount", required=True, help="Amount to dispense. Defaults to microAlgos.", default=1000000)
@click.option(
    "asset_title",
    "--asset",
    "-asa",
    type=click.Choice(list(assets.keys())),
    default="ALGO",
    help="Name of the asset to dispense. Defaults to ALGO.",
)
@click.option(
    "--ci",
    "ci",
    is_flag=True,
    default=False,
    help="Enable/disable interactions with Dispenser API via CI access token.",
)
def dispense_command(*, wallet: str, amount: int, asset_title: str, ci: bool) -> None:
    if not ci and not is_authenticated():
        logger.error("Please login first")
        return

    response = process_dispenser_request(
        url_suffix="dispense",
        data={"walletAddress": wallet, "amount": amount, "assetID": assets[asset_title]["asset_id"]},
        ci=ci,
        method="GET",
    )

    if response:
        logger.info(response.json()["message"])


@account_group.command("refund", help="Refund algo or asa back to a dispenser wallet")
@click.option("--txID", "tx_id", required=True, help="Transaction ID of your refund operation")
@click.option(
    "--ci", is_flag=True, default=False, help="Enable/disable interactions with Dispenser API via CI access token."
)
def refund_command(*, tx_id: str, ci: bool) -> None:
    response = process_dispenser_request(url_suffix="refund", data={"refundTxnID": tx_id}, ci=ci)

    if response:
        logger.info({response.json()["message"]})


@account_group.command(
    "current-limit", help="Get information about current withdrawal limits on your account (reset daily)"
)
@click.option(
    "--assetID",
    "asset_id",
    required=False,
    default=0,
    type=int,
    help="Specify asset ID explicitly. Defaults to ALGO.",
)
@click.option(
    "--ci", is_flag=True, default=False, help="Enable/disable interactions with Dispenser API via CI access token."
)
def get_withdrawal_limit(*, asset_id: int, ci: bool) -> None:
    url_suffix = f"user-limit/{asset_id}"
    response = process_dispenser_request(url_suffix=url_suffix, data={}, ci=ci, method="GET")

    if response:
        logger.info(f"Remaining daily withdrawal limit: {response.json()['amount']}")


@click.command("logout", help="Logout account from Dispenser API access")
def logout_command() -> None:
    """Logout from the Dispenser API access."""
    if is_authenticated():
        try:
            keyring.delete_password(KEYRING_NAMESPACE, KEYRING_KEY)
        except Exception as e:
            logger.debug(f"Error logging out {e}")
        logger.info("Logged out")
    else:
        logger.info("Not logged in! To login, run `algokit account login`")


@account_group.command("logout", help="Logout account from Dispenser API access")
@click.pass_context
def account_logout_command(context: click.Context) -> None:
    context.invoke(logout_command)


@click.command("login", help="Login account to access Dispenser API")
def login_command() -> None:
    """Login to the Dispenser API."""
    if is_authenticated():
        logger.info("Already authenticated")
        return

    token_data = get_oauth_tokens(api_audience=DispenseApiAudiences.USER, custom_scopes="offline_access")

    if not token_data:
        logger.error("Error during authentication")
        raise click.ClickException("Error getting the tokens")

    set_keyring_passwords(token_data)

    logger.info("Logged in!")


@account_group.command("login", help="Login account to access Dispenser API")
@click.pass_context
def account_login_command(context: click.Context) -> None:
    context.invoke(login_command)


@account_group.command("get-ci-token", help="Generate an access token for CI")
def get_ci_token_command() -> None:
    token_data = get_oauth_tokens(api_audience=DispenseApiAudiences.CI)

    if not token_data:
        logger.info("Error getting the tokens")
        raise click.ClickException("Error getting the tokens")

    token_file_path = "ci_token.txt"

    with Path.open(Path(token_file_path), "w") as token_file:
        token_file.write(token_data["access_token"])

    logger.info(f"CI access token generated and stored in {token_file_path}!")
    click.echo(
        f"Your CI access token has been saved to {token_file_path}.\
        Please ensure you keep this file safe or remove after copying the token!"
    )
