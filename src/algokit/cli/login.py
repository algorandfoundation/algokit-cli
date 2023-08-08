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
AUTH0_CLIENT_ID = "70kMcjtVcphvz33vSpvsU2OSOuAYgoxp"
ALGORITHMS = ["RS256"]
DISPENSER_URL = "provide dispenser api url here"


def refresh_token():
    refresh_token = keyring.get_password("algokit", "refresh_token")

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "authorization": f'Bearer {keyring.get_password("algokit", "access_token")}',
    }

    payload = f"grant_type=refresh_token&client_id={AUTH0_CLIENT_ID}&refresh_token={refresh_token}"

    response = requests.post(f"https://{AUTH0_DOMAIN}/oauth/token", data=payload, headers=headers)
    ok_code = 200

    if response.status_code != ok_code:
        logger.info("Error refreshing the token")
        raise click.ClickException("Error refreshing the token")

    token_data = response.json()

    keyring.set_password("algokit", "id_token", token_data["id_token"])
    keyring.set_password("algokit", "access_token", token_data["access_token"])


def validate_token(id_token: str):
    """
    Verify the token and its precedence

    :param id_token:
    """
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    issuer = f"https://{AUTH0_DOMAIN}/"
    sv = AsymmetricSignatureVerifier(jwks_url)
    tv = TokenVerifier(signature_verifier=sv, issuer=issuer, audience=AUTH0_CLIENT_ID)
    tv.verify(id_token)


def is_authenticated() -> bool:
    """
    Get the user email from the keyring

    :return:
    """
    id_token = keyring.get_password("algokit", "id_token")
    email = keyring.get_password("algokit", "email")

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


@click.command("dispense", help="Dummy api call")
@click.option("--wallet", help="Wallet address to dispense to")
@click.option("--ci", default=lambda: "CI" not in os.environ, help="Whether to load access token for ci invocation")
def dispense_command(*, wallet: str, ci: bool) -> None:
    url = f"{DISPENSER_URL}/dispense"

    # call passing access token as bearer
    token = keyring.get_password("algokit", "id_token") if not ci else keyring.get_password("algokit", "ci_token")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json={"walletAddress": wallet})
    logger.info(response.json()["message"])


@click.command("create-ci-token", help="Dummy create ci dispenser token api call")
def create_ci_token() -> None:
    if not is_authenticated():
        raise click.ClickException("Not authenticated")

    url = f"{DISPENSER_URL}/ci-token"

    # call passing access token as bearer
    headers = {"Authorization": f'Bearer {keyring.get_password("algokit", "id_token")}'}
    response = requests.post(url, headers=headers)
    keyring.set_password("algokit", "ci_token", response.json()["access_token"])


@click.command("logout", help="Logout of the dispenser")
def logout_command() -> None:
    keyring.delete_password("algokit", "id_token")
    keyring.delete_password("algokit", "access_token")
    keyring.delete_password("algokit", "refresh_token")
    keyring.delete_password("algokit", "email")
    logger.info("Logged out")


@click.command("login", help="Login with email to interact with TestNet dispenser.")
def login_command() -> None:
    if is_authenticated():
        logger.info("Already authenticated")
        return

    device_code_payload = {"client_id": AUTH0_CLIENT_ID, "scope": "openid profile email offline_access"}
    device_code_response = requests.post(f"https://{AUTH0_DOMAIN}/oauth/device/code", data=device_code_payload)
    success_code = 200

    if device_code_response.status_code != success_code:
        logger.info("Error generating the device code")
        raise click.ClickException("Error generating the device code")

    logger.info("Device code successful")
    device_code_data = device_code_response.json()
    logger.info(f"1. On your computer or mobile device navigate to: {device_code_data['verification_uri_complete']}")
    logger.info(f"2. Enter the following code: {device_code_data['user_code']}")

    token_payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device_code_data["device_code"],
        "client_id": AUTH0_CLIENT_ID,
    }

    authenticated = False
    while not authenticated:
        logger.info("Checking if the user completed the flow...")
        token_response = requests.post(f"https://{AUTH0_DOMAIN}/oauth/token", data=token_payload)

        token_data = token_response.json()
        ok_code = 200

        if token_response.status_code == ok_code:
            logger.info("Authenticated!")
            logger.info("- Id Token: {}...".format(token_data["id_token"][:10]))

            validate_token(token_data["id_token"])
            current_user = jwt.decode(
                token_data["id_token"], algorithms=ALGORITHMS, options={"verify_signature": False}
            )

            user_email = current_user.get("email")
            keyring.set_password("algokit", "id_token", token_data["id_token"])
            keyring.set_password("algokit", "access_token", token_data["access_token"])
            keyring.set_password("algokit", "refresh_token", token_data["refresh_token"])
            if user_email:
                keyring.set_password("algokit", "email", user_email)
                logger.info(f"User email: {user_email}")
            else:
                logger.warning("Email not found in the token")

            authenticated = True
        elif token_data["error"] not in ("authorization_pending", "slow_down"):
            logger.info(token_data["error_description"])
            raise click.ClickException(token_data["error_description"])
        else:
            time.sleep(device_code_data["interval"])
