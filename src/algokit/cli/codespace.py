import json
import logging
import subprocess
import tempfile
import time
from functools import cache
from pathlib import Path
from typing import Any

import click
import httpx

from algokit.core import proc
from algokit.core.sandbox import DEFAULT_NAME
from algokit.core.utils import is_windows, run_with_animation

logger = logging.getLogger(__name__)


def _install_gh() -> None:
    """Install gh if not already installed."""
    try:
        proc.run(["gh", "--version"])
    except Exception:
        logger.info("Installing gh...")
        try:
            if is_windows():
                proc.run(["winget", "install", "--id", "GitHub.cli", "--silent"])
            else:
                _install_gh_webi()
        except Exception as e:
            logger.error(f"Failed to automatically install gh cli: {e}")
            logger.error(
                "Please install `gh cli` manually by following official documentation at https://cli.github.com/"
            )
            raise
        logger.info("gh installed successfully!")


def _install_gh_webi() -> None:
    """Install gh via webi.sh script."""
    response = httpx.get("https://webi.sh/gh")
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=True, mode="w") as tmp_file:
        tmp_file.write(response.text)
        script_path = tmp_file.name
        Path(script_path).chmod(0o755)
        proc.run([script_path])


@cache
def _is_gh_authenticated() -> bool:
    """Check if user is authenticated with GitHub CLI."""
    try:
        result = proc.run(["gh", "auth", "status"])
        return "Logged in to" in result.output
    except subprocess.CalledProcessError:
        logger.error("GitHub CLI authentication check failed. Please login with `gh auth login`.")
        return False


def _perform_gh_login() -> bool:
    """Perform GitHub login for GitHub Codespace."""
    if _is_gh_authenticated():
        return True

    result = proc.run_interactive(
        ["gh", "auth", "login", "-s", "codespace"],
    )
    if result.exit_code != 0:
        logger.error("Failed to start LocalNet in GitHub Codespace")
        return False
    logger.info("Logged in to GitHub Codespace")
    return True


def _list_gh_codespaces() -> list[str]:
    """List available GitHub Codespaces."""
    if not _is_gh_authenticated():
        return []

    result = proc.run(["gh", "codespace", "list"], pass_stdin=True)

    if result.exit_code != 0:
        logger.error("Failed to log in to GitHub Codespaces")
        return []

    return [line.split("\t")[0] for line in result.output.splitlines()]


def _forward_ports(
    codespace_name: str, algod_port: int, kmd_port: int, indexer_port: int, max_retries: int = 5
) -> None:
    """Forwards ports with a maximum number of retries."""

    ports = [
        (algod_port, 4001),
        (kmd_port, 4002),
        (indexer_port, 8980),
    ]

    def _forward_one_attempt() -> proc.RunResult:
        command = [
            "gh",
            "codespace",
            "ports",
            "forward",
            "--codespace",
            codespace_name,
            *(f"{external_port}:{internal_port}" for internal_port, external_port in ports),
        ]

        return proc.run(command, pass_stdin=True, stdout_log_level=logging.INFO)

    for attempt in range(max_retries, 0, -1):
        result = _forward_one_attempt()
        if result:
            return
        logger.error("Port forwarding failed!")
        if attempt > 1:
            logger.info(f"Retrying ({attempt - 1} attempts left)...")
            time.sleep(10)

    raise Exception("All port forwarding attempts failed.")


def _delete_default_named_codespaces(codespaces: list[str], default_name: str) -> None:
    """
    Deletes GitHub Codespaces that start with the specified default name.

    :param codespaces: List of codespace names.
    :param default_name: The prefix to match for deletion.
    """
    for codespace in filter(lambda cs: cs.startswith(default_name), codespaces):
        proc.run(["gh", "codespace", "delete", "--codespace", codespace, "--force"], pass_stdin=True)
        logger.info(f"Deleted unused codespace {codespace}")


@click.group("codespace")
def codespace_group() -> None:
    """Manage the AlgoKit LocalNet in GitHub Codespaces."""
    _install_gh()


@codespace_group.command("start")
@click.option(
    "-m",
    "--machine",
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
    default=DEFAULT_NAME,
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
def start_localnet(  # noqa: PLR0913
    machine: str, algod_port: int, indexer_port: int, kmd_port: int, codespace_name: str, repo_url: str
) -> None:
    """Start the AlgoKit LocalNet in a GitHub Codespace."""
    if not _perform_gh_login():
        return

    codespaces = _list_gh_codespaces()

    # Delete existing codespaces with the default name
    _delete_default_named_codespaces(codespaces, DEFAULT_NAME)

    # Create a new codespace
    codespace_name = codespace_name or f"{DEFAULT_NAME}_{int(time.time())}"
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

    codespace_data: dict[str, Any] | None = None
    try:
        logger.info(f"Waiting for codespace {codespace_name} to be ready...")
        codespace_ready = False
        while not codespace_ready:
            run_with_animation(time.sleep, "Provisioning a codespace instance...", 60)
            status_result = proc.run(
                ["gh", "codespace", "list", "--json", "displayName", "--json", "state", "--json", "name"],
                pass_stdin=True,
            )
            try:
                codespace_data = next(
                    data for data in json.loads(status_result.output.strip()) if data["displayName"] == codespace_name
                )
            except StopIteration:
                run_with_animation(time.sleep, "Please wait...", 5)
                continue

            if status_result.exit_code == 0 and codespace_data and codespace_data["state"] == "Available":
                codespace_ready = True
                logger.info(f"Codespace {codespace_name} is now ready.")
                logger.warning(
                    "Keep the tab open during the LocalNet session. "
                    "Terminating the session will delete the codespace instance."
                )
                _forward_ports(codespace_data["name"], algod_port, kmd_port, indexer_port)

        logger.info("LocalNet started in GitHub Codespace")
    except KeyboardInterrupt:
        logger.warning("Termination in progress...")
        if codespace_data:
            logger.warning("Deleting the codespace...")
            proc.run(
                ["gh", "codespace", "delete", "--codespace", codespace_data["name"], "--force"],
                pass_stdin=True,
            )
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Exiting...")
