import json
import logging
import time
from typing import Any

import click

from algokit.core import proc, questionary_extensions
from algokit.core.codespace import ensure_gh_installed, forward_codespace_ports, get_gh_codespaces_list, login_to_gh
from algokit.core.utils import run_with_animation

logger = logging.getLogger(__name__)

CODESPACE_NAME_PREFIX = "algokit_codespace"
# Default timeout in seconds for creating a new codespace
# (~time needed for booting the container and then loading localnet)
CODESPACE_CREATE_TIMEOUT = 60
CODESPACE_CREATE_RETRY_TIMEOUT = 5


def _delete_default_named_codespaces(codespaces: list[str], default_name: str) -> None:
    """
    Deletes GitHub Codespaces that start with the specified default name.

    Args:
        codespaces (list[str]): List of codespace names.
        default_name (str): The prefix to match for deletion.
    """
    for codespace in filter(lambda cs: cs.startswith(default_name), codespaces):
        proc.run(["gh", "codespace", "delete", "--codespace", codespace, "--force"], pass_stdin=True)
        logger.info(f"Deleted unused codespace {codespace}")


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
    default=CODESPACE_NAME_PREFIX,
    required=False,
    help="The name of the codespace. Defaults to random name with timestamp.",
)
@click.option(
    "-r",
    "--repo-url",
    required=False,
    default="algorandfoundation/algokit-base-template",
    help="The URL of the repository. Defaults to algokit base template repo.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    required=False,
    default=False,
    type=click.BOOL,
    help=(
        "Force delete stale codespaces and skip confirmation prompts. "
        "Defaults to explicitly prompting for confirmation."
    ),
)
def codespace_command(  # noqa: PLR0913
    *, machine: str, algod_port: int, indexer_port: int, kmd_port: int, codespace_name: str, repo_url: str, force: bool
) -> None:
    """Manage the AlgoKit LocalNet in GitHub Codespaces."""
    ensure_gh_installed()

    if not login_to_gh():
        return

    codespaces = get_gh_codespaces_list()

    # Delete existing codespaces with the default name
    if codespaces and (
        force
        or questionary_extensions.prompt_confirm(
            f"Delete stale codespaces with `{CODESPACE_NAME_PREFIX}*` name prefix?", default=True
        )
    ):
        _delete_default_named_codespaces(codespaces, CODESPACE_NAME_PREFIX)

    # Create a new codespace
    codespace_name = codespace_name or f"{CODESPACE_NAME_PREFIX}_{int(time.time())}"
    proc.run(
        [
            "gh",
            "codespace",
            "create",
            "--repo",
            repo_url,
            "--display-name",
            codespace_name,
            "--machine",
            machine,
        ],
        pass_stdin=True,
    )
    run_with_animation(
        time.sleep,
        "Provisioning a new codespace instance...",
        CODESPACE_CREATE_TIMEOUT,
    )

    codespace_data: dict[str, Any] | None = None
    try:
        logger.info(f"Waiting for codespace {codespace_name} to be ready...")
        codespace_ready = False
        while not codespace_ready:
            status_result = proc.run(
                ["gh", "codespace", "list", "--json", "displayName", "--json", "state", "--json", "name"],
                pass_stdin=True,
            )
            try:
                codespace_data = next(
                    data for data in json.loads(status_result.output.strip()) if data["displayName"] == codespace_name
                )
            except StopIteration:
                run_with_animation(
                    time.sleep,
                    "Please wait...",
                    CODESPACE_CREATE_RETRY_TIMEOUT,
                )
                continue

            if status_result.exit_code == 0 and codespace_data and codespace_data["state"] == "Available":
                codespace_ready = True
                logger.info(f"Codespace {codespace_name} is now ready.")
                logger.warning(
                    "Keep the tab open during the LocalNet session. "
                    "Terminating the session will delete the codespace instance."
                )
                forward_codespace_ports(codespace_data["name"], algod_port, kmd_port, indexer_port)

        logger.info("LocalNet started in GitHub Codespace")
    except KeyboardInterrupt:
        logger.warning("Termination in progress...")
        if codespace_data and (force or questionary_extensions.prompt_confirm("Delete the codespace?", default=True)):
            logger.warning(f"Deleting the `{codespace_data['name']}` codespace...")
            proc.run(
                ["gh", "codespace", "delete", "--codespace", codespace_data["name"], "--force"],
                pass_stdin=True,
            )
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Exiting...")
