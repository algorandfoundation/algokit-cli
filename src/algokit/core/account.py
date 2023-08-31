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

logger = logging.getLogger(__name__)

# Constants
ALGORITHMS = ["RS256"]
KEYRING_NAMESPACE = "algokit_dispenser"
KEYRING_KEY = "algokit_account"
DISPENSER_REQUEST_TIMEOUT = 15


class DispenseApiAudiences(str, Enum):
    USER = "staging-dispenser-api-user "
    CI = "staging-dispenser-api-ci"


@dataclass
class AuthConfig:
    domain: str
    audiences: dict[DispenseApiAudiences, str]
    client_ids: dict[DispenseApiAudiences, str]
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
        DispenseApiAudiences.USER: "api-staging-dispenser-user",
        DispenseApiAudiences.CI: "api-staging-dispenser-ci",
    },
    client_ids={
        DispenseApiAudiences.USER: "flwPVx0HstfeZtGd3ZJVSwhGCFlR5v8a",
        DispenseApiAudiences.CI: "q3EWUsOmj5jINIchDxnm9gMEa10Th7Zj",
    },
    base_url="https://2i2vncra6a.execute-api.us-east-1.amazonaws.com",
)


def get_auth_token(*, ci: bool) -> str | None:
    """Retrieve the authorization token based on the environment"""
    if ci:
        return os.environ.get("CI_ACCESS_TOKEN")

    try:
        return get_keyring_data().access_token
    except Exception as ex:
        raise Exception("Token not found") from ex


def process_dispenser_request(
    *, url_suffix: str, data: dict | None = None, ci: bool, method: str = "POST"
) -> httpx.Response | None:
    """Generalized method to process http requests to dispenser API"""

    if not ci and not is_authenticated():
        logger.error("Please login first")
        return None

    headers = {"Authorization": f"Bearer {get_auth_token(ci=ci)}"}

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
    decoded_id_token = jwt.decode(token_data["id_token"], algorithms=ALGORITHMS, options={"verify_signature": False})
    user_id = decoded_id_token.get("sub")
    data = AccountKeyringData(
        id_token=token_data["id_token"],
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token", ""),
        user_id=user_id or "",
    )
    keyring.set_password(KEYRING_NAMESPACE, KEYRING_KEY, json.dumps(data.__dict__))


def get_keyring_data() -> AccountKeyringData:
    data_str = keyring.get_password(KEYRING_NAMESPACE, KEYRING_KEY)
    if not data_str:
        raise Exception("No keyring data found")
    return AccountKeyringData(**json.loads(data_str))


def validate_id_token(id_token: str, audience: str) -> None:
    jwks_url = f"https://{AUTH_CONFIG.domain}/.well-known/jwks.json"
    issuer = f"https://{AUTH_CONFIG.domain}/"
    sv = AsymmetricSignatureVerifier(jwks_url)
    tv = TokenVerifier(signature_verifier=sv, issuer=issuer, audience=audience)
    tv.verify(id_token)


def is_authenticated() -> bool:
    try:
        data = get_keyring_data()
    except Exception:
        return False
    decoded_token = jwt.decode(data.access_token, options={"verify_signature": False})
    return bool(time.time() < decoded_token.get("exp", 0))


def refresh_token() -> None:
    data = get_keyring_data()
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "authorization": f"Bearer {data.access_token}",
    }
    token_data = {
        "grant_type": "refresh_token",
        "client_id": AUTH_CONFIG.client_ids[DispenseApiAudiences.USER],
        "refresh_token": data.refresh_token,
    }
    response = httpx.post(
        f"https://{AUTH_CONFIG.domain}/oauth/token", data=token_data, headers=headers, timeout=DISPENSER_REQUEST_TIMEOUT
    )
    if response.status_code != httpx.codes.OK:
        logger.warning("Error refreshing the token")
        raise Exception("Error refreshing the token")
    set_keyring_passwords(response.json())


def get_oauth_tokens(api_audience: DispenseApiAudiences, custom_scopes: str | None = None) -> dict[str, Any] | None:
    scope = f"openid profile email {AUTH_CONFIG.audiences[api_audience]} " + (custom_scopes or "")
    device_code_payload = {
        "client_id": AUTH_CONFIG.client_ids[api_audience],
        "scope": scope.strip(),
        "audience": AUTH_CONFIG.audiences[api_audience],
    }

    device_code_response = httpx.post(
        f"https://{AUTH_CONFIG.domain}/oauth/device/code", data=device_code_payload, timeout=DISPENSER_REQUEST_TIMEOUT
    )

    if device_code_response.status_code != httpx.codes.OK:
        logger.info("Error generating the device code")
        return None

    device_code_data = device_code_response.json()
    logger.info(f"Navigate to: {device_code_data['verification_uri_complete']}")
    logger.info(f"Enter code: {device_code_data['user_code']}")

    authenticated = False
    token_data = None
    while not authenticated:
        token_payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code_data["device_code"],
            "client_id": AUTH_CONFIG.client_ids[api_audience],
            "audience": AUTH_CONFIG.audiences[api_audience],
        }

        token_response = httpx.post(
            f"https://{AUTH_CONFIG.domain}/oauth/token", data=token_payload, timeout=DISPENSER_REQUEST_TIMEOUT
        )

        token_data = token_response.json()
        if token_response.status_code == httpx.codes.OK and isinstance(token_data, dict):
            validate_id_token(token_data["id_token"], audience=AUTH_CONFIG.client_ids[api_audience])
            return token_data
        elif token_data["error"] not in ("authorization_pending", "slow_down"):
            logger.info(token_data["error_description"])
            raise Exception(token_data["error_description"])
        else:
            time.sleep(device_code_data["interval"])

    return None
