import json
import logging
import os
import signal
import subprocess
import time
from functools import cache
from subprocess import CalledProcessError

import click

from algokit.core import proc
from algokit.core.conf import get_app_config_dir
from algokit.core.sandbox import (
    DEFAULT_NAME,
)
from algokit.core.utils import find_valid_pipx_command, is_windows

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
        pipx_command = find_valid_pipx_command(
            "Unable to find pipx install so that `gh` static analyzer can be installed; "
            "please install pipx via https://pypa.github.io/pipx/ "
            "and then try `algokit task analyze ...` again."
        )
        proc.run(
            [*pipx_command, "install", "gh"],
            bad_return_code_error_message=(
                "Unable to install gh via pipx; please install gh " "manually and try `algokit task analyze ...` again."
            ),
        )
        logger.info("gh installed successfully via pipx!")


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
            stdout_log_level=logging.INFO,
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
        stdout_log_level=logging.INFO,
        prefix_process=False,
        pass_stdin=True,
    )

    if result.exit_code != 0:
        logger.error("Failed to list GitHub Codespaces")
        return []

    return [line.split("\t")[0] for line in result.output.splitlines()]


def run_detached_and_save_pid(command: list[str]) -> int:
    """
    Runs a command in detached mode and saves its PID to a file.

    Args:
        command (list): The command to run as a list of strings.

    Returns:
        int: The PID of the detached process.
    """
    kill_process()
    pid_file_path = get_app_config_dir() / "codespace.sandbox.pid"

    # Create a detached process and capture its PID
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, start_new_session=True
    )

    # Adjustments for detaching the process
    with open(os.devnull, "wb") as devnull:
        process = subprocess.Popen(
            command, stdout=devnull, stderr=devnull, stdin=devnull, close_fds=True, start_new_session=True
        )

    try:
        # Save the PID to a file
        with pid_file_path.open("w") as pidfile:
            pidfile.write(str(process.pid))
    finally:
        # The process is already detached due to start_new_session=True
        pass

    return process.pid


def kill_process():
    """
    Kills the process with the PID stored in the given file.

    """

    pid_file_path = get_app_config_dir() / "codespace.sandbox.pid"

    if not pid_file_path.exists():
        return

    with pid_file_path.open("rb") as pidfile:
        try:
            pid = int(pidfile.read().strip())
            if is_windows():
                subprocess.Popen(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                os.killpg(pid, signal.SIGTERM)
        except Exception:
            logger.debug("Failed to kill process with PID", exc_info=True)
            return


@click.group("codespace", short_help="Manage the AlgoKit LocalNet in GitHub Codespaces.")
def codespace_group() -> None:
    _install_gh_if_needed()


@codespace_group.command("start", short_help="Start the AlgoKit LocalNet.")
def start_localnet() -> None:
    # Logic to start LocalNet in a GitHub Codespace
    if not _perform_gh_login():
        return

    codespaces = _list_gh_codespaces()

    if codespaces:
        for codespace in codespaces:
            if codespace.startswith(DEFAULT_NAME):
                result = proc.run(
                    ["gh", "codespace", "delete", "--codespace", codespace, "--force"],
                    stdout_log_level=logging.INFO,
                    prefix_process=False,
                    pass_stdin=False,
                )
                if result.exit_code != 0:
                    logger.error(f"Failed to delete codespace {codespace}")
                    return

    codespace_name = f"{DEFAULT_NAME}_{time.time()}"
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
        stdout_log_level=logging.INFO,
        prefix_process=False,
        pass_stdin=False,
    )
    if result.exit_code != 0:
        logger.error("Failed to start LocalNet in GitHub Codespace")
        raise click.ClickException(result.output)
    logger.info(f"Waiting for codespace {codespace_name} to be ready...")
    codespace_ready = False
    while not codespace_ready:
        time.sleep(10)  # Poll every 10 seconds
        status_result = proc.run(
            ["gh", "codespace", "list", "--json", "displayName", "--json", "state"],
            stdout_log_level=logging.DEBUG,
            prefix_process=False,
            pass_stdin=False,
        )
        if status_result.exit_code == 0 and json.loads(status_result.output.strip())["state"] == "Available":
            codespace_ready = True
            logger.info(f"Codespace {codespace_name} is now ready.")
            result = proc.run(
                [
                    "gh",
                    "codespace",
                    "ports",
                    "forward",
                    "--codespace",
                    f"{codespace_name}",
                    "4001:4001",
                    "4002:4002",
                    "8980:8980",
                ],
                stdout_log_level=logging.INFO,
                prefix_process=False,
                pass_stdin=True,
            )
        else:
            logger.debug(f"Codespace {codespace_name} is not ready yet. Current state: {status_result.output.strip()}")

    logger.info("LocalNet started in GitHub Codespace")
