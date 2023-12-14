import logging
from pathlib import Path

import click

from algokit.core.tasks.ipfs import (
    MAX_FILE_SIZE,
    PinataBadRequestError,
    PinataForbiddenError,
    PinataHttpError,
    PinataInternalServerError,
    PinataUnauthorizedError,
    get_pinata_jwt,
    set_pinata_jwt,
    upload_to_pinata,
)
from algokit.core.utils import run_with_animation

logger = logging.getLogger(__name__)


@click.group(
    "ipfs",
)
def ipfs_group() -> None:
    """Upload files to IPFS using Pinata provider."""


@ipfs_group.command("login", help="Login to Pinata ipfs provider. You will be prompted for your JWT.")
def login_command() -> None:
    pinata_jwt = get_pinata_jwt()
    if pinata_jwt:
        logger.warning("You are already logged in!")
        return
    else:
        logger.info(
            "Follow the instructions on https://docs.pinata.cloud/docs/getting-started "
            "to create an account and obtain a JWT."
        )
        set_pinata_jwt(click.prompt("Enter pinata JWT", hide_input=True, confirmation_prompt=True, type=str))
        logger.info("Login successful")


@ipfs_group.command("logout", help="Logout of Pinata ipfs provider.")
def logout_command() -> None:
    pinata_jwt = get_pinata_jwt()
    if pinata_jwt:
        set_pinata_jwt(None)
        logger.info("Logout successful")
        return
    else:
        logger.warning("Already logged out")


@ipfs_group.command("upload", help="Upload a file to Pinata ipfs provider. Please note, max file size is 100MB.")
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
    pinata_jwt = get_pinata_jwt()
    if not pinata_jwt:
        raise click.ClickException("You are not logged in! Please login using `algokit task ipfs login`.")

    try:
        total = file_path.stat().st_size
        if total > MAX_FILE_SIZE:
            raise click.ClickException("File size exceeds 100MB limit!")

        def upload() -> str:
            return upload_to_pinata(file_path, pinata_jwt, name)

        cid = run_with_animation(
            target_function=upload,
            animation_text="Uploading",
        )
        logger.info(f"File uploaded successfully!\n CID: {cid}")

    except click.ClickException as ex:
        raise ex
    except OSError as ex:
        logger.debug(ex)
        raise click.ClickException("Failed to open file!") from ex
    except (
        PinataBadRequestError,
        PinataUnauthorizedError,
        PinataForbiddenError,
        PinataInternalServerError,
        PinataHttpError,
    ) as ex:
        logger.debug(ex)
        raise click.ClickException(repr(ex)) from ex
    except Exception as ex:
        logger.debug(ex)
        raise click.ClickException("Failed to upload file!") from ex
