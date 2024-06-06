import logging
import subprocess
from time import time
from typing import Any

import click

from algokit.core import questionary_extensions
from algokit.core.codespace import (
    CODESPACE_NAME_PREFIX,
    authenticate_with_github,
    create_codespace,
    delete_codespace,
    delete_codespaces_with_prefix,
    ensure_github_cli_installed,
    forward_ports_for_codespace,
    is_codespace_ready,
    list_github_codespaces,
)

logger = logging.getLogger(__name__)

# https://docs.github.com/en/codespaces/setting-your-user-preferences/setting-your-timeout-period-for-github-codespaces
MIN_GH_PORT_FORWARD_TIMEOUT_MIN = 1
MAX_GH_PORT_FORWARD_TIMEOUT_MIN = 24


def _validate_idle_timeout(_ctx: click.Context, _param: click.Parameter, value: int) -> int:
    if value < MIN_GH_PORT_FORWARD_TIMEOUT_MIN or value > MAX_GH_PORT_FORWARD_TIMEOUT_MIN:
        raise click.BadParameter(
            f"Timeout must be between {MIN_GH_PORT_FORWARD_TIMEOUT_MIN} and {MAX_GH_PORT_FORWARD_TIMEOUT_MIN} hours."
        )
    return value


@click.command("codespace")
@click.option(
    "-m",
    "--machine",
    type=click.Choice(
        ["basicLinux32gb", "standardLinux32gb", "premiumLinux", "largePremiumLinux"], case_sensitive=True
    ),
    default="basicLinux32gb",
    required=False,
    help="The GitHub Codespace machine type to use. Defaults to base tier.",
)
@click.option(
    "-a", "--algod-port", default=4001, required=False, help="The port for the Algorand daemon. Defaults to 4001."
)
@click.option(
    "-i", "--indexer-port", default=8980, required=False, help="The port for the Algorand indexer. Defaults to 8980."
)
@click.option("-k", "--kmd-port", default=4002, required=False, help="The port for the Algorand kmd. Defaults to 4002.")
@click.option(
    "-n",
    "--codespace-name",
    default="",
    required=False,
    help=f"The name of the codespace. Defaults to '{CODESPACE_NAME_PREFIX}_timestamp'.",
)
@click.option(
    "-r",
    "--repo-url",
    required=False,
    default="algorandfoundation/algokit-base-template",
    help="The URL of the repository. Defaults to algokit base template repo.",
)
@click.option(
    "-t",
    "--timeout",
    "timeout_hours",
    default=1,
    required=False,
    callback=_validate_idle_timeout,
    help="Default max runtime timeout in hours. Upon hitting the timeout a codespace will be shutdown to "
    "prevent accidental spending over GitHub Codespaces quota. Defaults to 1 hour.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    required=False,
    default=False,
    type=click.BOOL,
    help=(
        "Force delete previously used codespaces with `{CODESPACE_NAME_PREFIX}*` name prefix and skip prompts. "
        "Defaults to explicitly prompting for confirmation."
    ),
)
def codespace_command(  # noqa: PLR0913
    *,
    machine: str,
    algod_port: int,
    indexer_port: int,
    kmd_port: int,
    codespace_name: str,
    repo_url: str,
    timeout_hours: int,
    force: bool,
) -> None:
    """Manage the AlgoKit LocalNet in GitHub Codespaces."""
    ensure_github_cli_installed()

    if not authenticate_with_github():
        return

    codespaces = list_github_codespaces()

    # Delete existing codespaces with the default name
    if codespaces and (
        force
        or questionary_extensions.prompt_confirm(
            f"Delete previously used codespaces with `{CODESPACE_NAME_PREFIX}*` name prefix?", default=True
        )
    ):
        delete_codespaces_with_prefix(codespaces, CODESPACE_NAME_PREFIX)

    # Create a new codespace
    codespace_name = codespace_name or f"{CODESPACE_NAME_PREFIX}_{int(time())}"
    create_codespace(repo_url, codespace_name, machine)

    codespace_data: dict[str, Any] | None = None

    try:
        logger.info(f"Waiting for codespace {codespace_name} to be ready...")
        codespace_data = is_codespace_ready(codespace_name)
        if not codespace_data:
            raise RuntimeError("Error creating codespace. Please check your internet connection and try again.")

        logger.info(f"Codespace {codespace_name} is now ready.")
        logger.warning(
            "Keep the terminal open during the LocalNet session. "
            "Terminating the session will delete the codespace instance."
        )

        forward_ports_for_codespace(codespace_data["name"], algod_port, kmd_port, indexer_port, timeout_hours * 60 * 60)
        logger.info("LocalNet started in GitHub Codespace")

    except subprocess.TimeoutExpired:
        logger.warning("Timeout reached. Shutting down the codespace...")
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt received. Shutting down the codespace...")
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Exiting...")
        if codespace_data:
            delete_codespace(codespace_data=codespace_data, force=force)
