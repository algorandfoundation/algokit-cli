import logging
import os
import time

import click
import jwt
import keyring
import requests
from auth0.authentication.token_verifier import AsymmetricSignatureVerifier, TokenVerifier

logger = logging.getLogger(__name__)

# Below are public identifiers (not secrets, safe to have in vcs)
# TODO: Move these to a config file
AUTH0_DOMAIN = "dev-lwqrjgkkdkekto3q.au.auth0.com"
AUTH0_USER_CLIENT_ID = "70kMcjtVcphvz33vSpvsU2OSOuAYgoxp"
AUTH0_CI_CLIENT_ID = "4QagPR1QhaIoIoOXzoU9R12BfQ76vO5Z"
DISPENSER_BASE_URL = "set url"
AUTH0_AUDIENCE = DISPENSER_BASE_URL
ALGORITHMS = ["RS256"]
KEYRING_NAMESPACE = "algokit"


def get_oauth_tokens(*, client_id: str = AUTH0_USER_CLIENT_ID, extra_scopes: str | None = None) -> None:
    scope = "openid profile email " + (extra_scopes or "")
    device_code_payload = {
        "client_id": client_id,
        "scope": scope.strip(),
        "audience": AUTH0_AUDIENCE,
    }
    device_code_response = requests.post(f"https://{AUTH0_DOMAIN}/oauth/device/code", data=device_code_payload)
    success_code = 200

    if device_code_response.status_code != success_code:
        logger.info("Error generating the device code")
        raise click.ClickException("Error generating the device code")

    device_code_data = device_code_response.json()
    logger.info(f"1. On your computer or mobile device navigate to: {device_code_data['verification_uri_complete']}")
    logger.info(f"2. Enter the following code: {device_code_data['user_code']}")

    token_payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device_code_data["device_code"],
        "client_id": client_id,
        "audience": AUTH0_AUDIENCE,
    }

    authenticated = False
    token_data = None
    while not authenticated:
        logger.info("Checking if the user completed the flow...")
        token_response = requests.post(f"https://{AUTH0_DOMAIN}/oauth/token", data=token_payload)

        token_data = token_response.json()
        ok_code = 200

        if token_response.status_code == ok_code:
            validate_id_token(
                token_data["id_token"], audience=AUTH0_USER_CLIENT_ID if "user" in scope else AUTH0_CI_CLIENT_ID
            )

            return token_data

        elif token_data["error"] not in ("authorization_pending", "slow_down"):
            logger.info(token_data["error_description"])
            raise click.ClickException(token_data["error_description"])
        else:
            time.sleep(device_code_data["interval"])

    return None


def refresh_token():
    refresh_token = keyring.get_password(KEYRING_NAMESPACE, "refresh_token")

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "authorization": f'Bearer {keyring.get_password(KEYRING_NAMESPACE, "access_token")}',
    }

    payload = f"grant_type=refresh_token&client_id={AUTH0_USER_CLIENT_ID}&refresh_token={refresh_token}"

    response = requests.post(f"https://{AUTH0_DOMAIN}/oauth/token", data=payload, headers=headers)
    ok_code = 200

    if response.status_code != ok_code:
        logger.warning("Error refreshing the token")
        raise click.ClickException("Error refreshing the token")

    token_data = response.json()

    keyring.set_password(KEYRING_NAMESPACE, "id_token", token_data["id_token"])
    keyring.set_password(KEYRING_NAMESPACE, "access_token", token_data["access_token"])
    if "refresh_token" in token_data:
        keyring.set_password(KEYRING_NAMESPACE, "refresh_token", token_data["refresh_token"])


def validate_id_token(id_token: str, audience: str):
    """
    Verify the token and its precedence

    :param id_token:
    """
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    issuer = f"https://{AUTH0_DOMAIN}/"
    sv = AsymmetricSignatureVerifier(jwks_url)
    tv = TokenVerifier(signature_verifier=sv, issuer=issuer, audience=audience)
    tv.verify(id_token)


def is_authenticated() -> bool:
    """
    Get the user email from the keyring

    :return:
    """
    id_token = keyring.get_password(KEYRING_NAMESPACE, "id_token")
    email = keyring.get_password(KEYRING_NAMESPACE, "email")

    if not id_token or not email:
        return False

    decoded_token = jwt.decode(id_token, options={"verify_signature": False})

    try:
        if time.time() < decoded_token["exp"]:
            return True
        else:
            refresh_token()
            return True
    except Exception:
        return False


@click.group("account")
def account_group() -> None:
    """Account based commands"""


@account_group.command("dispense", help="Dispense funds to a wallet")
@click.option("--wallet", help="Wallet address to dispense to")
@click.option("--amount", help="Amount to dispense", default=1000000)
@click.option(
    "--ci", is_flag=True, default=lambda: "CI" in os.environ, help="Whether to load access token for ci invocation"
)
def dispense_command(*, wallet: str, amount: int, ci: bool) -> None:
    if not is_authenticated():
        logger.error("Please login first")
        return

    url = f"{DISPENSER_BASE_URL}/dispense"

    # call passing access token as bearer
    token = (
        keyring.get_password(KEYRING_NAMESPACE, "access_token") if not ci else os.environ.get("ALGOKIT_CI_ACCESS_TOKEN")
    )

    if not token:
        raise click.ClickException("Token not found")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json={"walletAddress": wallet, "amount": amount})
    logger.info(response.json()["message"])


@account_group.command("logout", help="Logout of the dispenser")
def logout_command() -> None:
    keyring.delete_password(KEYRING_NAMESPACE, "id_token")
    keyring.delete_password(KEYRING_NAMESPACE, "access_token")
    keyring.delete_password(KEYRING_NAMESPACE, "refresh_token")
    keyring.delete_password(KEYRING_NAMESPACE, "email")
    logger.info("Logged out")


@account_group.command("login", help="Login with email to interact with TestNet dispenser.")
def login_command() -> None:
    if is_authenticated():
        logger.info("Already authenticated")
        return

    token_data = get_oauth_tokens(client_id=AUTH0_USER_CLIENT_ID, extra_scopes="context:user-request offline_access")

    if not token_data:
        logger.error("Error during authentication")
        raise click.ClickException("Error getting the tokens")

    current_user = jwt.decode(token_data["id_token"], algorithms=ALGORITHMS, options={"verify_signature": False})

    user_email = current_user.get("email")
    keyring.set_password(KEYRING_NAMESPACE, "id_token", token_data["id_token"])
    keyring.set_password(KEYRING_NAMESPACE, "access_token", token_data["access_token"])
    if "refresh_token" in token_data:
        keyring.set_password(KEYRING_NAMESPACE, "refresh_token", token_data["refresh_token"])

    if user_email:
        keyring.set_password(KEYRING_NAMESPACE, "email", user_email)
        logger.info(f"Account {user_email} authenticated!")
    else:
        logger.warning("Email not found in the token")


@account_group.command("get-ci-token", help="Generate an access token for CI")
def get_ci_token_command() -> None:
    token_data = get_oauth_tokens(client_id=AUTH0_CI_CLIENT_ID, extra_scopes="context:ci-request")

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
