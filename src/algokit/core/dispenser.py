import base64
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
import jwt
import keyring
from auth0.authentication.token_verifier import AsymmetricSignatureVerifier, TokenVerifier
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)

# Constants
ALGORITHMS = ["RS256"]
DISPENSER_KEYRING_NAMESPACE = "algokit_dispenser"
DISPENSER_KEYRING_KEY = "algokit_account"
DISPENSER_REQUEST_TIMEOUT = 15
DISPENSER_ACCESS_TOKEN_KEY = "DISPENSER_ACCESS_TOKEN"


class DispenserApiAudiences(str, Enum):
    USER = "staging-dispenser-api-user"
    CI = "staging-dispenser-api-ci"


@dataclass
class AuthConfig:
    domain: str
    audiences: dict[DispenserApiAudiences, str]
    client_ids: dict[DispenserApiAudiences, str]
    base_url: str


@dataclass
class AccountKeyringData:
    id_token: str
    access_token: str
    refresh_token: str
    user_id: str


AUTH_CONFIG = AuthConfig(
    domain="dispenser-staging.eu.auth0.com",
    audiences={
        DispenserApiAudiences.USER: "api-staging-dispenser-user",
        DispenserApiAudiences.CI: "api-staging-dispenser-ci",
    },
    client_ids={
        DispenserApiAudiences.USER: "flwPVx0HstfeZtGd3ZJVSwhGCFlR5v8a",
        DispenserApiAudiences.CI: "q3EWUsOmj5jINIchDxnm9gMEa10Th7Zj",
    },
    base_url="https://api.dispenser-dev.algorandfoundation.tools",
)
AUTH_JWKS_URL = f"https://{AUTH_CONFIG.domain}/.well-known/jwks.json"


def _get_dispenser_credentials() -> AccountKeyringData:
    """
    Get dispenser account credentials from the keyring.
    """

    data_str = keyring.get_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_KEY)
    if not data_str:
        raise Exception("No keyring data found")
    return AccountKeyringData(**json.loads(data_str))


def _get_auth_token(*, ci: bool) -> str | None:
    """
    Retrieve the authorization token based on the environment
    """

    if ci:
        return os.environ.get(DISPENSER_ACCESS_TOKEN_KEY)

    try:
        return _get_dispenser_credentials().access_token
    except Exception as ex:
        raise Exception("Token not found") from ex


def _validate_jwt_id_token(id_token: str, audience: str) -> None:
    """
    Validate the id token.
    """

    sv = AsymmetricSignatureVerifier(AUTH_JWKS_URL)
    tv = TokenVerifier(signature_verifier=sv, issuer=f"https://{AUTH_CONFIG.domain}/", audience=audience)
    tv.verify(id_token)


def _get_access_token_rsa_pub_key(access_token: str) -> rsa.RSAPublicKey:
    """
    Fetch the RSA public key based on provided access token.
    """
    jwks_url = f"https://{AUTH_CONFIG.domain}/.well-known/jwks.json"
    jwks = httpx.get(jwks_url).json()
    for key in jwks["keys"]:
        if key["kid"] == jwt.get_unverified_header(access_token)["kid"]:
            return rsa.RSAPublicNumbers(
                e=int.from_bytes(base64.urlsafe_b64decode(key["e"] + "=="), byteorder="big"),
                n=int.from_bytes(base64.urlsafe_b64decode(key["n"] + "=="), byteorder="big"),
            ).public_key()

    raise Exception("No matching key found")


def _refresh_user_access_token() -> None:
    """
    Refresh the user access token.
    """

    data = _get_dispenser_credentials()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {data.access_token}",
    }
    token_data = {
        "grant_type": "refresh_token",
        "client_id": AUTH_CONFIG.client_ids[DispenserApiAudiences.USER],
        "refresh_token": data.refresh_token,
    }
    response = httpx.post(
        f"https://{AUTH_CONFIG.domain}/oauth/token", data=token_data, headers=headers, timeout=DISPENSER_REQUEST_TIMEOUT
    )
    response.raise_for_status()

    set_keyring_passwords(response.json())


def _request_device_code(api_audience: DispenserApiAudiences, custom_scopes: str | None = None) -> dict[str, Any]:
    """
    Request a device code for user authentication.
    """

    scope = f"openid profile email {AUTH_CONFIG.audiences[api_audience]} {custom_scopes or ''}".strip()
    device_code_payload = {
        "client_id": AUTH_CONFIG.client_ids[api_audience],
        "scope": scope,
        "audience": AUTH_CONFIG.audiences[api_audience],
    }
    response = httpx.post(
        f"https://{AUTH_CONFIG.domain}/oauth/device/code", data=device_code_payload, timeout=DISPENSER_REQUEST_TIMEOUT
    )
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict):
        logger.debug("Expected a dictionary response from OAuth token request, got: %s", type(data).__name__)
        raise Exception("Unexpected response type from OAuth device code request")

    return data


def request_token(api_audience: DispenserApiAudiences, device_code: str) -> dict[str, Any]:
    """
    Request OAuth tokens.
    """

    token_payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device_code,
        "client_id": AUTH_CONFIG.client_ids[api_audience],
        "audience": AUTH_CONFIG.audiences[api_audience],
    }
    response = httpx.post(
        f"https://{AUTH_CONFIG.domain}/oauth/token", data=token_payload, timeout=DISPENSER_REQUEST_TIMEOUT
    )

    data = response.json()
    if not isinstance(data, dict):
        logger.debug(f"Expected a dictionary response from OAuth token request, got: {type(data).__name__}")
        raise Exception("Unexpected response type from OAuth token request")

    return data


def process_dispenser_request(
    *, url_suffix: str, data: dict | None = None, ci: bool, method: str = "POST"
) -> httpx.Response:
    """
    Generalized method to process http requests to dispenser API
    """

    headers = {"Authorization": f"Bearer {_get_auth_token(ci=ci)}"}

    # Set request arguments
    request_args = {
        "url": f"{AUTH_CONFIG.base_url}/{url_suffix}",
        "headers": headers,
        "timeout": DISPENSER_REQUEST_TIMEOUT,
    }

    if method.upper() != "GET" and data is not None:
        request_args["json"] = data

    try:
        response: httpx.Response = getattr(httpx, method.lower())(**request_args)
        return response
    except Exception as err:
        error_message = "Error processing dispenser API request"
        logger.debug(f"{error_message}: {err}", exc_info=True)
        raise Exception(error_message) from err


def set_keyring_passwords(token_data: dict[str, str]) -> None:
    """
    Set the keyring passwords.
    """

    decoded_id_token = jwt.decode(token_data["id_token"], algorithms=ALGORITHMS, options={"verify_signature": False})
    user_id = decoded_id_token.get("sub")
    data = AccountKeyringData(
        id_token=token_data["id_token"],
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token", ""),
        user_id=user_id or "",
    )
    keyring.set_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_KEY, json.dumps(data.__dict__))


def is_authenticated() -> bool:
    """
    Check if the user is authenticated by checking if the token is still valid.
    If the token is expired, attempt to refresh it.
    """

    try:
        data = _get_dispenser_credentials()
        rsa_pub_key = _get_access_token_rsa_pub_key(data.access_token)

        jwt.decode(
            data.access_token,
            rsa_pub_key,
            options={"verify_signature": True},
            algorithms=ALGORITHMS,
            audience=AUTH_CONFIG.audiences[DispenserApiAudiences.USER],
        )

        return True
    except jwt.ExpiredSignatureError:
        logger.debug("Access token is expired. Attempting to refresh the token...")

        try:
            _refresh_user_access_token()
            return True
        except Exception:
            logger.warning("Failed to refresh the access token. Retrying login...", exc_info=True)

        return False
    except Exception as ex:
        logger.debug(f"Access token validation error: {ex}", exc_info=True)
        return False


def revoke_refresh_token() -> None:
    """
    Revoke the refresh token.
    """

    data = _get_dispenser_credentials()

    if not data.refresh_token:
        logger.debug("No refresh token found, nothing to revoke.")
        return

    url = f"https://{AUTH_CONFIG.domain}/oauth/revoke"
    payload = {"token": data.refresh_token, "client_id": AUTH_CONFIG.client_ids[DispenserApiAudiences.USER]}
    headers = {"content-type": "application/json"}

    try:
        response = httpx.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.debug("Token revoked successfully")
    except httpx.HTTPStatusError as ex:
        raise Exception(f"Failed to revoke token: {ex}") from ex
    except Exception as ex:
        raise Exception(f"An unexpected error occurred: {ex}") from ex


def get_oauth_tokens(api_audience: DispenserApiAudiences, custom_scopes: str | None = None) -> dict[str, Any] | None:
    """
    Authenticate and get OAuth tokens.
    """

    device_code_data = _request_device_code(api_audience, custom_scopes)

    if not device_code_data:
        return None

    logger.info(f"Navigate to: {device_code_data['verification_uri_complete']}")
    logger.info(f"Confirm code: {device_code_data['user_code']}")

    start_time = time.time()
    timeout_interval = 300  # 5 minutes
    while True:
        token_data = request_token(api_audience, device_code_data["device_code"])

        if "id_token" in token_data:
            _validate_jwt_id_token(token_data["id_token"], audience=AUTH_CONFIG.client_ids[api_audience])
            return token_data

        error = token_data.get("error", "")
        if error not in ("authorization_pending", "slow_down"):
            raise Exception(token_data.get("error_description", ""))

        # Check if 5 minutes have passed
        if time.time() - start_time > timeout_interval:
            logger.warning("Authentication cancelled. Timeout reached after 5 minutes of inactivity.")
            break

        time.sleep(device_code_data.get("interval", 5))

    return None
