import json
import logging
import tempfile
import time
from functools import cache
from pathlib import Path
from subprocess import CalledProcessError

import click
import httpx

from algokit.core import proc
from algokit.core.sandbox import (
    DEFAULT_NAME,
)
from algokit.core.utils import is_windows, run_with_animation

logger = logging.getLogger(__name__)


def _install_gh_if_needed() -> None:
    """
    Install gh if it's not already installed.
    """
    try:
        proc.run(
            ["gh", "--version"],
            bad_return_code_error_message="gh --version failed, please check your gh install",
        )
    except Exception as e:
        logger.debug(e)
        logger.info("gh not found; attempting to install it...")
        if is_windows():
            proc.run(
                ["winget", "install", "--id", "GitHub.cli", "--silent"],
                bad_return_code_error_message=(
                    "Unable to install gh via winget; please install gh "
                    "manually and try `algokit localnet codespace` again."
                ),
            )
        else:
            script_path = None
            try:
                # Download the script
                response = httpx.get(
                    "https://webi.sh/gh",
                )
                response.raise_for_status()

                # Save the script to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp_file:
                    tmp_file.write(response.text)
                    script_path = tmp_file.name

                # Make the script executable
                Path(script_path).chmod(0o755)

                # Execute the script
                proc.run(
                    [script_path],
                    bad_return_code_error_message=(
                        "Unable to install gh via webi installer script; please install gh "
                        "manually and try `algokit task analyze ...` again."
                    ),
                )
                logger.info("gh installed successfully via webi installer script!")
            finally:
                # Clean up the temporary file
                if script_path and "script_path" in locals():
                    Path(script_path).unlink()


@cache
def _is_gh_authenticated() -> bool:
    """
    Private method to check if the user is authenticated with GitHub CLI (gh).

    Returns:
        bool: True if authenticated, False otherwise.
    """
    try:
        result = proc.run(
            ["gh", "auth", "status"],
            stdout_log_level=logging.DEBUG,
            prefix_process=False,
            pass_stdin=True,
        )
        if "Logged in to" in result.output:
            return True
    except CalledProcessError:
        logger.error("GitHub CLI authentication check failed. Please ensure you are logged in with `gh auth login`.")
    return False


def _perform_gh_login() -> bool:
    if _is_gh_authenticated():
        return True

    result = proc.run(
        ["gh", "auth", "login", "-s", "codespace"],
        stdout_log_level=logging.INFO,
        prefix_process=False,
        pass_stdin=True,
    )
    if result.exit_code != 0:
        logger.error("Failed to start LocalNet in GitHub Codespace")
        return False
    logger.info("Logged in to GitHub Codespace")
    return True


def _list_gh_codespaces() -> list[str]:
    if not _is_gh_authenticated():
        return []

    result = proc.run(
        ["gh", "codespace", "list"],
        stdout_log_level=logging.DEBUG,
        prefix_process=False,
        pass_stdin=True,
    )

    if result.exit_code != 0:
        logger.error("Failed to list GitHub Codespaces")
        return []

    return [line.split("\t")[0] for line in result.output.splitlines()]


@click.group("codespace", short_help="Manage the AlgoKit LocalNet in GitHub Codespaces.")
def codespace_group() -> None:
    _install_gh_if_needed()


@codespace_group.command("start", short_help="Start the AlgoKit LocalNet.")
def start_localnet() -> None:
    """
    Logic to start LocalNet in a GitHub Codespace.
    """

    codespace_data = None
    try:
        if not _perform_gh_login():
            return

        codespaces = _list_gh_codespaces()

        # Delete existing codespaces that match the default name
        for codespace in filter(lambda cs: cs.startswith(DEFAULT_NAME), codespaces):
            result = proc.run(
                ["gh", "codespace", "delete", "--codespace", codespace, "--force"],
                stdout_log_level=logging.DEBUG,
                prefix_process=False,
                pass_stdin=False,
            )
            if result.exit_code != 0:
                logger.error(f"Failed to delete codespace {codespace}")
                return

        # Create a new codespace
        codespace_name: str = f"{DEFAULT_NAME}_{int(time.time())}"
        result = proc.run(
            [
                "gh",
                "codespace",
                "create",
                "--repo",
                "algorandfoundation/algokit-base-template",
                "--display-name",
                codespace_name,
                "--machine",
                "basicLinux32gb",
            ],
            stdout_log_level=logging.DEBUG,
            prefix_process=False,
            pass_stdin=False,
        )
        if result.exit_code != 0:
            logger.error("Failed to start LocalNet in GitHub Codespace")
            raise click.ClickException(result.output)

        # Wait for the codespace to be ready
        logger.info(f"Waiting for codespace {codespace_name} to be ready...")
        codespace_ready: bool = False
        while not codespace_ready:
            run_with_animation(
                time.sleep,
                "Provisioning a codespace instance...",
                60,
            )  # Poll every 60 seconds
            status_result = proc.run(
                ["gh", "codespace", "list", "--json", "displayName", "--json", "state", "--json", "name"],
                stdout_log_level=logging.DEBUG,
                prefix_process=False,
                pass_stdin=False,
            )
            try:
                codespace_data = next(
                    data for data in json.loads(status_result.output.strip()) if data["displayName"] == codespace_name
                )
            except StopIteration:
                logger.debug(f"No data found for codespace {codespace_name}.")
                continue

            if status_result.exit_code == 0 and codespace_data["state"] == "Available":
                codespace_ready = True
                logger.info(f"Codespace {codespace_name} is now ready.")
                # Forward necessary ports
                logger.warning(
                    "Keep the tab open during the LocalNet session. Terminating the session "
                    "will delete the codespace instance. For persistent scenarios, use 'algokit localnet start', "
                    "which utilizes docker."
                )
                proc.run(
                    [
                        "gh",
                        "codespace",
                        "ports",
                        "forward",
                        "--codespace",
                        codespace_data["name"],
                        "4001:4001",
                        "4002:4002",
                        "8980:8980",
                    ],
                    stdout_log_level=logging.INFO,
                    prefix_process=False,
                    pass_stdin=True,
                )

            else:
                logger.debug(
                    f"Codespace {codespace_name} is not ready yet. Current state: {status_result.output.strip()}"
                )

        logger.info("LocalNet started in GitHub Codespace")
    except KeyboardInterrupt as e:
        logger.warning("Terminating in progress...", exc_info=True)
        if codespace_data:
            logger.warning("Deleting the codespace...")
            proc.run(
                ["gh", "codespace", "delete", "--codespace", codespace_data["name"], "--force"],
                stdout_log_level=logging.INFO,
                prefix_process=False,
                pass_stdin=True,
            )
        raise click.Abort from e
