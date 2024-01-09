import json
import logging
from pathlib import Path

import httpx
import keyring

logger = logging.getLogger(__name__)

ALGOKIT_PINATA_NAMESPACE = "algokit_pinata"
ALGOKIT_PINATA_TOKEN_KEY = "algokit_pinata_access_token"

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
DEFAULT_TIMEOUT = 90


class PinataError(Exception):
    """Base class for Piñata errors."""

    def __init__(self, response: httpx.Response):
        self.response = response
        super().__init__(f"Pinata error: {response.status_code}")

    def __str__(self) -> str:
        return f"Pinata error: {self.response.status_code}. {self.response.text}"


class PinataBadRequestError(PinataError):
    pass


class PinataUnauthorizedError(PinataError):
    pass


class PinataForbiddenError(PinataError):
    pass


class PinataInternalServerError(PinataError):
    pass


class PinataHttpError(PinataError):
    pass


def get_pinata_jwt() -> str | None:
    """
    Retrieves a password from the keyring library using the
    ALGOKIT_PINATA_NAMESPACE and ALGOKIT_PINATA_TOKEN_KEY variables.

    Returns:
        str | None: The retrieved password from the keyring, or None if no password is found.
    """
    try:
        old_api_key = keyring.get_password("algokit_web3_storage", "algokit_web3_storage_access_token")
        if old_api_key:
            logger.warning(
                "You are using the old Web3 Storage API key. Please login again using `algokit task ipfs login` with "
                "Pinata ipfs provider. Follow the instructions on https://docs.pinata.cloud/docs/getting-started"
                "to create an account and obtain a JWT."
            )
            keyring.delete_password("algokit_web3_storage", "algokit_web3_storage_access_token")
    except Exception:
        pass
    return keyring.get_password(ALGOKIT_PINATA_NAMESPACE, ALGOKIT_PINATA_TOKEN_KEY)


def set_pinata_jwt(jwt: str | None) -> None:
    """
    Sets or deletes a password in the keyring library based on the provided JWT.

    Args:
        jwt (str | None): The JWT to be set in the keyring library. If None, the password will be deleted.

    Returns:
        None
    """
    if jwt:
        keyring.set_password(ALGOKIT_PINATA_NAMESPACE, ALGOKIT_PINATA_TOKEN_KEY, jwt)
    else:
        keyring.delete_password(ALGOKIT_PINATA_NAMESPACE, ALGOKIT_PINATA_TOKEN_KEY)


def upload_to_pinata(file_path: Path, jwt: str, name: str | None = None) -> str:
    """
    Uploads a file to the Piñata API.

    Args:
        file_path (Path): The path to the file that needs to be uploaded.
        jwt (str): The JWT for accessing the Piñata API.
        name (str | None, optional): The name to be assigned to the uploaded file. If not provided,
        the name of the file at `file_path` will be used. Defaults to None.
        If not provided, the content will be read from the file at `file_path`. Defaults to None.

    Returns:
        str: The CID (Content Identifier) of the uploaded file.

    Raises:
        ValueError: If the CID is not a string.
        PinataBadRequestError: If there is a bad request error.
        PinataUnauthorizedError: If there is an unauthorized error.
        PinataForbiddenError: If there is a forbidden error.
        PinataInternalServerError: If there is an internal server error.
        PinataHttpError: If there is an HTTP error.

    Example Usage:
        file_path = Path("path/to/file.txt")
        jwt = "your_jwt"
        name = "file.txt"

        cid = upload_to_pinata(file_path, jwt, name)
        print(cid) # e.g. "bafybeih6z7z2z3z4z5z6z7z8z9z0"
    """

    with file_path.open("rb") as file:
        file_content = file.read()

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {jwt}",
    }

    pinata_options = {"cidVersion": "1"}
    data = {"pinataOptions": json.dumps(pinata_options)}
    files = {"file": (name or file_path.name, file_content)}
    try:
        response = httpx.post(
            url="https://api.pinata.cloud/pinning/pinFileToIPFS",
            data=data,
            files=files,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )

        response.raise_for_status()
        cid = response.json().get("IpfsHash")
        if not isinstance(cid, str):
            raise ValueError("IpfsHash is not a string.")
        return cid
    except httpx.HTTPStatusError as ex:
        if ex.response.status_code == httpx.codes.BAD_REQUEST:
            raise PinataBadRequestError(ex.response) from ex
        if ex.response.status_code == httpx.codes.UNAUTHORIZED:
            raise PinataUnauthorizedError(ex.response) from ex
        if ex.response.status_code == httpx.codes.FORBIDDEN:
            raise PinataForbiddenError(ex.response) from ex
        if ex.response.status_code == httpx.codes.INTERNAL_SERVER_ERROR:
            raise PinataInternalServerError(ex.response) from ex

        raise PinataHttpError(ex.response) from ex
