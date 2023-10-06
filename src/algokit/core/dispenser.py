import base64
import contextlib
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar

import httpx
import jwt
import keyring
from auth0.authentication.token_verifier import AsymmetricSignatureVerifier, TokenVerifier
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)

# Constants
ALGORITHMS = ["RS256"]
DISPENSER_KEYRING_NAMESPACE = "algokit_dispenser"
DISPENSER_KEYRING_ID_TOKEN_KEY = "algokit_dispenser_id_token"
DISPENSER_KEYRING_ACCESS_TOKEN_KEY = "algokit_dispenser_access_token"
DISPENSER_KEYRING_REFRESH_TOKEN_KEY = "algokit_dispenser_refresh_token"
DISPENSER_KEYRING_USER_ID_KEY = "algokit_dispenser_user_id"
DISPENSER_REQUEST_TIMEOUT = 15
DISPENSER_ACCESS_TOKEN_KEY = "ALGOKIT_DISPENSER_ACCESS_TOKEN"
DISPENSER_LOGIN_TIMEOUT = 300  # 5 minutes


class DispenserApiAudiences(str, Enum):
    USER = "user"
    CI = "ci"


@dataclass
class AccountKeyringData:
    id_token: str
    access_token: str
    refresh_token: str
    user_id: str


class ApiConfig:
    BASE_URL = "https://api.dispenser.algorandfoundation.tools"


class AuthConfig:
    DOMAIN = "dispenser-prod.eu.auth0.com"
    BASE_URL = f"https://{DOMAIN}"
    JWKS_URL = f"{BASE_URL}/.well-known/jwks.json"
    OAUTH_TOKEN_URL = f"{BASE_URL}/oauth/token"
    OAUTH_DEVICE_CODE_URL = f"{BASE_URL}/oauth/device/code"
    OAUTH_REVOKE_URL = f"{BASE_URL}/oauth/revoke"
    AUDIENCES: ClassVar[dict[str, str]] = {
        DispenserApiAudiences.USER: "api-prod-dispenser-user",
        DispenserApiAudiences.CI: "api-prod-dispenser-ci",
    }
    CLIENT_IDS: ClassVar[dict[str, str]] = {
        DispenserApiAudiences.USER: "UKcJQcqFaZRQvik45QW5lsSRERUf8Ub6",
        DispenserApiAudiences.CI: "BOZkxGUiiWkaAXZebCQ20MTIYuQSqqpI",
    }


class APIErrorCode:
    DISPENSER_OUT_OF_FUNDS = "dispenser_out_of_funds"
    FORBIDDEN = "forbidden"
    FUND_LIMIT_EXCEEDED = "fund_limit_exceeded"
    DISPENSER_ERROR = "dispenser_error"
    MISSING_PARAMETERS = "missing_params"
    AUTHORIZATION_ERROR = "authorization_error"
    REPUTATION_REFRESH_FAILED = "reputation_refresh_failed"
    TXN_EXPIRED = "txn_expired"
    TXN_INVALID = "txn_invalid"
    TXN_ALREADY_PROCESSED = "txn_already_processed"
    INVALID_ASSET = "invalid_asset"
    UNEXPECTED_ERROR = "unexpected_error"


def _get_dispenser_credential(key: str) -> str:
    """
    Get dispenser account credentials from the keyring.
    """

    response = keyring.get_password(DISPENSER_KEYRING_NAMESPACE, key)

    if not response:
        raise Exception(f"No keyring data found for key: {key}")

    return response


def _get_dispenser_credentials() -> AccountKeyringData:
    """
    Get dispenser account credentials from the keyring.
    """

    id_token = _get_dispenser_credential(DISPENSER_KEYRING_ID_TOKEN_KEY)
    access_token = _get_dispenser_credential(DISPENSER_KEYRING_ACCESS_TOKEN_KEY)
    refresh_token = _get_dispenser_credential(DISPENSER_KEYRING_REFRESH_TOKEN_KEY)
    user_id = _get_dispenser_credential(DISPENSER_KEYRING_USER_ID_KEY)

    return AccountKeyringData(
        id_token=id_token, access_token=access_token, refresh_token=refresh_token, user_id=user_id
    )


def _get_auth_token() -> str:
    """
    Retrieve the authorization token based on the environment.
    CI environment variables take precedence over keyring.
    """
    try:
        ci_access_token = os.environ.get(DISPENSER_ACCESS_TOKEN_KEY)

        if ci_access_token:
            logger.debug("Using CI access token over keyring credentials")

        return ci_access_token if ci_access_token else _get_dispenser_credentials().access_token
    except Exception as ex:
        raise Exception("Token not found") from ex


def _validate_jwt_id_token(id_token: str, audience: str) -> None:
    """
    Validate the id token.
    """

    sv = AsymmetricSignatureVerifier(AuthConfig.JWKS_URL)
    tv = TokenVerifier(signature_verifier=sv, issuer=f"{AuthConfig.BASE_URL}/", audience=audience)
    tv.verify(id_token)


def _get_access_token_rsa_pub_key(access_token: str) -> rsa.RSAPublicKey:
    """
    Fetch the RSA public key based on provided access token.
    """
    jwks = httpx.get(AuthConfig.JWKS_URL).json()
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
        "client_id": AuthConfig.CLIENT_IDS[DispenserApiAudiences.USER],
        "refresh_token": data.refresh_token,
    }
    response = httpx.post(
        AuthConfig.OAUTH_TOKEN_URL, data=token_data, headers=headers, timeout=DISPENSER_REQUEST_TIMEOUT
    )
    response.raise_for_status()

    set_dispenser_credentials(response.json())


def _request_device_code(api_audience: DispenserApiAudiences, custom_scopes: str | None = None) -> dict[str, Any]:
    """
    Request a device code for user authentication.
    """

    scope = f"openid profile email {custom_scopes or ''}".strip()
    device_code_payload = {
        "client_id": AuthConfig.CLIENT_IDS[api_audience],
        "scope": scope,
        "audience": AuthConfig.AUDIENCES[api_audience],
    }
    response = httpx.post(AuthConfig.OAUTH_DEVICE_CODE_URL, data=device_code_payload, timeout=DISPENSER_REQUEST_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict):
        logger.debug("Expected a dictionary response from OAuth token request, got: %s", type(data).__name__)
        raise Exception("Unexpected response type from OAuth device code request")

    return data


def _get_hours_until_reset(resets_at: str) -> float:
    now_utc = datetime.now(timezone.utc)
    reset_date = datetime.strptime(resets_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    return round((reset_date - now_utc).total_seconds() / 3600, 1)


def request_token(api_audience: DispenserApiAudiences, device_code: str) -> dict[str, Any]:
    """
    Request OAuth tokens.
    """

    token_payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device_code,
        "client_id": AuthConfig.CLIENT_IDS[api_audience],
        "audience": AuthConfig.AUDIENCES[api_audience],
    }
    response = httpx.post(AuthConfig.OAUTH_TOKEN_URL, data=token_payload, timeout=DISPENSER_REQUEST_TIMEOUT)

    data = response.json()
    if not isinstance(data, dict):
        logger.debug(f"Expected a dictionary response from OAuth token request, got: {type(data).__name__}")
        raise Exception("Unexpected response type from OAuth token request")

    return data


def process_dispenser_request(*, url_suffix: str, data: dict | None = None, method: str = "POST") -> httpx.Response:
    """
    Generalized method to process http requests to dispenser API
    """

    headers = {"Authorization": f"Bearer {_get_auth_token()}"}

    # Set request arguments
    request_args = {
        "url": f"{ApiConfig.BASE_URL}/{url_suffix}",
        "headers": headers,
        "timeout": DISPENSER_REQUEST_TIMEOUT,
    }

    if method.upper() != "GET" and data is not None:
        request_args["json"] = data

    try:
        response: httpx.Response = getattr(httpx, method.lower())(**request_args)
        response.raise_for_status()
        return response

    except httpx.HTTPStatusError as err:
        error_message = f"Error processing dispenser API request: {err.response.status_code}"
        error_response = None
        with contextlib.suppress(Exception):
            error_response = err.response.json()

        if error_response and error_response.get("code") == APIErrorCode.FUND_LIMIT_EXCEEDED:
            hours_until_reset = _get_hours_until_reset(error_response.get("resetsAt"))
            error_message = (
                "Limit exceeded. "
                f"Try again in ~{hours_until_reset} hours if your request doesn't exceed the daily limit."
            )

        elif err.response.status_code == httpx.codes.BAD_REQUEST:
            error_message = err.response.json()["message"]

        raise Exception(error_message) from err

    except Exception as err:
        error_message = "Error processing dispenser API request"
        logger.debug(f"{error_message}: {err}", exc_info=True)
        raise err


def set_dispenser_credentials(token_data: dict[str, str]) -> None:
    """
    Set the keyring passwords.
    """

    # Verify signature is set to false since we already validate id_tokens in _validate_jwt_id_token
    decoded_id_token = jwt.decode(token_data["id_token"], algorithms=ALGORITHMS, options={"verify_signature": False})

    keyring.set_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_ID_TOKEN_KEY, token_data["id_token"])
    keyring.set_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_ACCESS_TOKEN_KEY, token_data["access_token"])
    keyring.set_password(
        DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_REFRESH_TOKEN_KEY, token_data.get("refresh_token", "")
    )
    keyring.set_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_USER_ID_KEY, decoded_id_token.get("sub"))


def clear_dispenser_credentials() -> None:
    """
    Clear the keyring passwords.
    """

    keyring.delete_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_ID_TOKEN_KEY)
    keyring.delete_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_ACCESS_TOKEN_KEY)
    keyring.delete_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_REFRESH_TOKEN_KEY)
    keyring.delete_password(DISPENSER_KEYRING_NAMESPACE, DISPENSER_KEYRING_USER_ID_KEY)


def is_authenticated() -> bool:
    """
    Check if the user is authenticated by checking if the token is still valid.
    If the token is expired, attempt to refresh it.
    """

    try:
        access_token = _get_auth_token()
        rsa_pub_key = _get_access_token_rsa_pub_key(access_token)

        jwt.decode(
            access_token,
            rsa_pub_key,
            options={"verify_signature": True},
            algorithms=ALGORITHMS,
            audience=[
                AuthConfig.AUDIENCES[DispenserApiAudiences.USER],
                AuthConfig.AUDIENCES[DispenserApiAudiences.CI],
            ],
        )

        return True
    except jwt.ExpiredSignatureError:
        logger.debug("Access token is expired. Attempting to refresh the token...")

        try:
            _refresh_user_access_token()
            return True
        except Exception:
            logger.warning(
                "Failed to refresh the access token. Please authenticate first before proceeding with this command.",
                exc_info=True,
            )

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

    payload = {"token": data.refresh_token, "client_id": AuthConfig.CLIENT_IDS[DispenserApiAudiences.USER]}
    headers = {"content-type": "application/json"}

    try:
        response = httpx.post(AuthConfig.OAUTH_REVOKE_URL, json=payload, headers=headers)
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
    while True:
        token_data = request_token(api_audience, device_code_data["device_code"])

        if "id_token" in token_data:
            _validate_jwt_id_token(token_data["id_token"], audience=AuthConfig.CLIENT_IDS[api_audience])
            return token_data

        error = token_data.get("error", "")
        if error not in ("authorization_pending", "slow_down"):
            raise Exception(token_data.get("error_description", ""))

        # Check if 5 minutes have passed
        if time.time() - start_time > DISPENSER_LOGIN_TIMEOUT:
            logger.warning("Authentication cancelled. Timeout reached after 5 minutes of inactivity.")
            break

        time.sleep(device_code_data.get("interval", 5))

    return None
