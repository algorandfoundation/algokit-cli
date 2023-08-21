import logging
import time
from enum import Enum
from typing import Any

import click
import httpx
import jwt
import keyring
from auth0.authentication.token_verifier import AsymmetricSignatureVerifier, TokenVerifier

logger = logging.getLogger(__name__)


class DispenseApiScopes(str, Enum):
    USER = "dispenser_user"
    CI = "dispenser_ci"


AUTH0_AUDIENCE = {
    DispenseApiScopes.USER.value: "https://al-dev.dispenser-user.com",
    DispenseApiScopes.CI.value: "https://al-dev.dispenser-ci.com",
}

AUTH0_DOMAIN = "dev-lwqrjgkkdkekto3q.au.auth0.com"
AUTH0_USER_CLIENT_ID = "70kMcjtVcphvz33vSpvsU2OSOuAYgoxp"
AUTH0_CI_CLIENT_ID = "4QagPR1QhaIoIoOXzoU9R12BfQ76vO5Z"
DISPENSER_BASE_URL = ""
ALGORITHMS = ["RS256"]
KEYRING_NAMESPACE = "algokit"
DISPENSER_REQUEST_TIMEOUT = 15


def set_keyring_passwords(token_data: dict[str, str], user_id: str | None = None) -> None:
    keyring.set_password(KEYRING_NAMESPACE, "id_token", token_data["id_token"])
    keyring.set_password(KEYRING_NAMESPACE, "access_token", token_data["access_token"])
    if "refresh_token" in token_data:
        keyring.set_password(KEYRING_NAMESPACE, "refresh_token", token_data["refresh_token"])
    if user_id:
        keyring.set_password(KEYRING_NAMESPACE, "user_id", user_id)


def get_oauth_tokens(
    *, client_id: str = AUTH0_USER_CLIENT_ID, api_scope: str, extra_scopes: str | None = None
) -> dict[str, Any] | None:
    scope = f"openid profile email {api_scope} " + (extra_scopes or "")
    device_code_payload = {
        "client_id": client_id,
        "scope": scope.strip(),
        "audience": AUTH0_AUDIENCE[api_scope],
    }
    device_code_response = httpx.post(
        f"https://{AUTH0_DOMAIN}/oauth/device/code", data=device_code_payload, timeout=DISPENSER_REQUEST_TIMEOUT
    )
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
        "audience": AUTH0_AUDIENCE[api_scope],
    }

    authenticated = False
    token_data = None
    while not authenticated:
        logger.info("Checking if the user completed the flow...")
        token_response = httpx.post(
            f"https://{AUTH0_DOMAIN}/oauth/token", data=token_payload, timeout=DISPENSER_REQUEST_TIMEOUT
        )

        token_data = token_response.json()
        ok_code = 200

        if token_response.status_code == ok_code:
            token_data = token_response.json()
            if isinstance(token_data, dict):
                validate_id_token(
                    token_data["id_token"], audience=AUTH0_USER_CLIENT_ID if "user" in scope else AUTH0_CI_CLIENT_ID
                )
                return token_data
            else:
                raise ValueError("Unexpected response format")

        elif token_data["error"] not in ("authorization_pending", "slow_down"):
            logger.info(token_data["error_description"])
            raise click.ClickException(token_data["error_description"])
        else:
            time.sleep(device_code_data["interval"])

    return None


def refresh_token() -> None:
    refresh_token = keyring.get_password(KEYRING_NAMESPACE, "refresh_token")

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "authorization": f'Bearer {keyring.get_password(KEYRING_NAMESPACE, "access_token")}',
    }

    data = {
        "grant_type": "refresh_token",
        "client_id": AUTH0_USER_CLIENT_ID,
        "refresh_token": refresh_token,
    }

    response = httpx.post(
        f"https://{AUTH0_DOMAIN}/oauth/token", data=data, headers=headers, timeout=DISPENSER_REQUEST_TIMEOUT
    )
    ok_code = 200

    if response.status_code != ok_code:
        logger.warning("Error refreshing the token")
        raise click.ClickException("Error refreshing the token")

    token_data = response.json()

    set_keyring_passwords(token_data)


def validate_id_token(id_token: str, audience: str) -> None:
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
    user_id = keyring.get_password(KEYRING_NAMESPACE, "user_id")

    if not id_token or not user_id:
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
