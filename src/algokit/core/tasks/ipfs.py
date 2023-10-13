import logging
from collections.abc import Generator
from pathlib import Path

import httpx
import keyring

logger = logging.getLogger(__name__)

ALGOKIT_WEB3_STORAGE_NAMESPACE = "algokit_web3_storage"
ALGOKIT_WEB3_STORAGE_TOKEN_KEY = "algokit_web3_storage_access_token"

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_CHUNK_SIZE = 1024 * 1024  # 1MB
DEFAULT_TIMEOUT = 10


class Web3StorageError(Exception):
    """Base class for Web3 Storage errors."""

    def __init__(self, response: httpx.Response):
        self.response = response
        super().__init__(f"Web3 Storage error: {response.status_code}")

    def __str__(self) -> str:
        return f"Web3 Storage error: {self.response.status_code}. {self.response.text}"


class Web3StorageBadRequestError(Web3StorageError):
    pass


class Web3StorageUnauthorizedError(Web3StorageError):
    pass


class Web3StorageForbiddenError(Web3StorageError):
    pass


class Web3StorageInternalServerError(Web3StorageError):
    pass


class Web3StorageHttpError(Web3StorageError):
    pass


def get_web3_storage_api_key() -> str | None:
    """
    Retrieves a password from the keyring library using the
    ALGOKIT_WEB3_STORAGE_NAMESPACE and ALGOKIT_WEB3_STORAGE_TOKEN_KEY variables.

    Returns:
        str | None: The retrieved password from the keyring, or None if no password is found.
    """

    return keyring.get_password(ALGOKIT_WEB3_STORAGE_NAMESPACE, ALGOKIT_WEB3_STORAGE_TOKEN_KEY)


def set_web3_storage_api_key(api_key: str | None) -> None:
    """
    Sets or deletes a password in the keyring library based on the provided API key.

    Args:
        api_key (str | None): The API key to be set in the keyring library. If None, the password will be deleted.

    Returns:
        None
    """
    if api_key:
        keyring.set_password(ALGOKIT_WEB3_STORAGE_NAMESPACE, ALGOKIT_WEB3_STORAGE_TOKEN_KEY, api_key)
    else:
        keyring.delete_password(ALGOKIT_WEB3_STORAGE_NAMESPACE, ALGOKIT_WEB3_STORAGE_TOKEN_KEY)


def upload_to_web3_storage(
    file_path: Path, api_key: str, name: str | None = None, content: Generator | None = None
) -> str:
    """
    Uploads a file to the Web3 Storage API.

    Args:
        file_path (Path): The path to the file that needs to be uploaded.
        api_key (str): The API key for accessing the Web3 Storage API.
        name (str | None, optional): The name to be assigned to the uploaded file. If not provided,
        the name of the file at `file_path` will be used. Defaults to None.
        content (Generator | None, optional): A generator that yields the content of the file.
        If not provided, the content will be read from the file at `file_path`. Defaults to None.

    Returns:
        str: The CID (Content Identifier) of the uploaded file.

    Raises:
        ValueError: If the CID is not a string.
        Web3StorageBadRequestError: If there is a bad request error.
        Web3StorageUnauthorizedError: If there is an unauthorized error.
        Web3StorageForbiddenError: If there is a forbidden error.
        Web3StorageInternalServerError: If there is an internal server error.
        Web3StorageHttpError: If there is an HTTP error.

    Example Usage:
        file_path = Path("path/to/file.txt")
        api_key = "your_api_key"
        name = "file.txt"

        cid = upload_to_web3_storage(file_path, api_key, name)
        print(cid)  # e.g. "bafybeih6z7z2z3z4z5z6z7z8z9z0"
    """

    with file_path.open("rb") as file:
        file_content = file.read()
        num_chunks = file_path.stat().st_size // MAX_CHUNK_SIZE | 1
        timeout = DEFAULT_TIMEOUT * num_chunks
        logger.debug(f"Timeout set to {timeout} seconds based on {num_chunks} chunks.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Name": name or file_path.name,
    }

    try:
        response = httpx.post(
            "https://api.web3.storage/upload",
            headers=headers,
            timeout=timeout,
            content=content or file_content,
        )
        response.raise_for_status()
        cid = response.json().get("cid")
        if not isinstance(cid, str):
            raise ValueError("CID is not a string.")
        return cid
    except httpx.HTTPStatusError as ex:
        if ex.response.status_code == httpx.codes.BAD_REQUEST:
            raise Web3StorageBadRequestError(ex.response) from ex
        if ex.response.status_code == httpx.codes.UNAUTHORIZED:
            raise Web3StorageUnauthorizedError(ex.response) from ex
        if ex.response.status_code == httpx.codes.FORBIDDEN:
            raise Web3StorageForbiddenError(ex.response) from ex
        if ex.response.status_code == httpx.codes.INTERNAL_SERVER_ERROR:
            raise Web3StorageInternalServerError(ex.response) from ex

        raise Web3StorageHttpError(ex.response) from ex
