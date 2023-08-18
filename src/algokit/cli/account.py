import logging
import os

import click
import httpx
import jwt
import keyring

from algokit.core.account import (
    ALGORITHMS,
    AUTH0_CI_CLIENT_ID,
    AUTH0_USER_CLIENT_ID,
    DISPENSER_BASE_URL,
    DISPENSER_REQUEST_TIMEOUT,
    KEYRING_NAMESPACE,
    get_oauth_tokens,
    is_authenticated,
    set_keyring_passwords,
)

logger = logging.getLogger(__name__)

assets = {
    "ALGO": {
        "asset_id": 0,
        "decimals": 6,
        "description": "Algorand token on Algorand TestNet",
    },
    "USDC (Wormhole)": {
        "asset_id": 113638050,
        "decimals": 6,
        "description": "USDC token on Algorand TestNet via Wormhole",
    },
}


@click.group("account")
def account_group() -> None:
    """Account based commands"""


@account_group.command("dispense", help="Dispense funds to a wallet")
@click.option("--wallet", help="Wallet address to dispense to", callback=lambda _, __, value: value.strip("\"'"))
@click.option("--amount", help="Amount to dispense", default=1000000)
@click.option(
    "asset_title",
    "--asset",
    "-asa",
    type=click.Choice(list(assets.keys())),
    default="ALGO",
    help="Name of an official template to use. To see a list of descriptions, run this command with no arguments.",
)
@click.option(
    "--ci",
    is_flag=True,
    default=False,
    help="Enable/disable interactive prompts. If the CI environment variable is set, defaults to non-interactive",
)
def dispense_command(*, wallet: str, amount: int, asset_title: str, ci: bool) -> None:
    if not ci and not is_authenticated():
        logger.error("Please login first")
        return

    asset = assets[asset_title]

    url = f"{DISPENSER_BASE_URL}/dispense"

    # call passing access token as bearer
    token = (
        keyring.get_password(KEYRING_NAMESPACE, "access_token") if not ci else os.environ.get("ALGOKIT_CI_ACCESS_TOKEN")
    )

    if not token:
        raise click.ClickException("Token not found")

    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.post(
        url,
        headers=headers,
        json={"walletAddress": wallet, "amount": amount, "assetID": asset["asset_id"]},
        timeout=DISPENSER_REQUEST_TIMEOUT,
    )
    logger.info(response.json()["message"])


@account_group.command("logout", help="Logout of the dispenser")
def logout_command() -> None:
    for token in ("id_token", "access_token", "refresh_token", "email"):
        try:
            keyring.delete_password(KEYRING_NAMESPACE, token)
        except Exception as e:
            logger.debug(f"Error logging out {e} {token}")
    logger.info("Logged out")


@account_group.command("login", help="Login with email to interact with TestNet dispenser.")
def login_command() -> None:
    if is_authenticated():
        logger.info("Already authenticated")
        return

    token_data = get_oauth_tokens(client_id=AUTH0_USER_CLIENT_ID, extra_scopes="dispenser_user offline_access")

    if not token_data:
        logger.error("Error during authentication")
        raise click.ClickException("Error getting the tokens")

    current_user = jwt.decode(token_data["id_token"], algorithms=ALGORITHMS, options={"verify_signature": False})

    user_id = current_user.get("sub")
    set_keyring_passwords(token_data, user_id)


@account_group.command("get-ci-token", help="Generate an access token for CI")
def get_ci_token_command() -> None:
    token_data = get_oauth_tokens(client_id=AUTH0_CI_CLIENT_ID, extra_scopes="dispenser_ci")

    if not token_data:
        logger.info("Error getting the tokens")
        raise click.ClickException("Error getting the tokens")

    click.pause(
        info="Please note, token is not persisted by algokit-cli, make sure to store it somewhere safe after copying. Press any key to display it...",  # noqa: E501
        err=False,
    )
    click.echo("CI access token: " + token_data["access_token"])
    click.pause(info="Copy the token value and press any key to continue...", err=False)
    os.system("cls" if os.name == "nt" else "clear")  # clears the console

    logger.info("CI access token generated!")
