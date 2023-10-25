import logging
from collections.abc import Generator
from pathlib import Path

import click

from algokit.core.tasks.ipfs import (
    MAX_CHUNK_SIZE,
    MAX_FILE_SIZE,
    Web3StorageBadRequestError,
    Web3StorageForbiddenError,
    Web3StorageHttpError,
    Web3StorageInternalServerError,
    Web3StorageUnauthorizedError,
    get_web3_storage_api_key,
    set_web3_storage_api_key,
    upload_to_web3_storage,
)

logger = logging.getLogger(__name__)


@click.group(
    "ipfs",
)
def ipfs_group() -> None:
    """Upload files to IPFS using Web3 Storage provider."""


@ipfs_group.command("login", help="Login to web3 storage ipfs provider.")
def login_command() -> None:
    web3_storage_api_key = get_web3_storage_api_key()
    if web3_storage_api_key:
        logger.warning("You are already logged in!")
        return
    else:
        logger.info(
            "Follow the instructions on https://web3.storage/docs/intro/#get-an-api-token "
            "to create an account and obtain an API token."
        )
        set_web3_storage_api_key(
            click.prompt("Enter web3 storage API token", hide_input=True, confirmation_prompt=True, type=str)
        )


@ipfs_group.command("logout", help="Logout of web3 storage ipfs provider.")
def logout_command() -> None:
    web3_storage_api_key = get_web3_storage_api_key()
    if web3_storage_api_key:
        set_web3_storage_api_key(None)
        logger.info("Logout successful")
        return
    else:
        logger.warning("Already logged out")


@ipfs_group.command("upload", help="Upload a file to web3 storage ipfs provider. Please note, max file size is 100MB.")
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, path_type=Path),
    help="Path to the file to upload.",
)
@click.option(
    "--name",
    "-n",
    "name",
    required=False,
    type=click.STRING,
    help="Human readable name for this upload, for use in file listings.",
)
def upload(file_path: Path, name: str | None) -> None:
    web3_storage_api_key = get_web3_storage_api_key()
    if not web3_storage_api_key:
        raise click.ClickException("You are not logged in! Please login using `algokit ipfs login`.")

    try:
        with file_path.open("rb") as file:
            total = file_path.stat().st_size

            if total > MAX_FILE_SIZE:
                raise click.ClickException("File size exceeds 100MB limit!")

            with click.progressbar(length=total, label="Uploading file") as bar:  # type: ignore[var-annotated]

                def read_file_in_chunks() -> Generator[bytes, None, None]:
                    while data := file.read(MAX_CHUNK_SIZE):
                        yield data
                        bar.update(len(data))

                cid = upload_to_web3_storage(file_path, web3_storage_api_key, name, read_file_in_chunks())
                logger.info(f"\nFile uploaded successfully!\nCID: {cid}")
    except click.ClickException as ex:
        raise ex
    except OSError as ex:
        logger.debug(ex)
        raise click.ClickException("Failed to open file!") from ex
    except (
        Web3StorageBadRequestError,
        Web3StorageUnauthorizedError,
        Web3StorageForbiddenError,
        Web3StorageInternalServerError,
        Web3StorageHttpError,
    ) as ex:
        logger.debug(ex)
        raise click.ClickException(repr(ex)) from ex
    except Exception as ex:
        logger.debug(ex)
        raise click.ClickException("Failed to upload file!") from ex
