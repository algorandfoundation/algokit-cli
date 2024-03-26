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
        if is_windows():
            proc.run(["winget", "install", "--id", "GitHub.cli", "--silent"])
        else:
            _install_gh_webi()
        logger.info("gh installed successfully!")


def _install_gh_webi() -> None:
    """Install gh via webi.sh script."""
    script_path = None
    try:
        response = httpx.get("https://webi.sh/gh")
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp_file:
            tmp_file.write(response.text)
            script_path = tmp_file.name

        Path(script_path).chmod(0o755)
        proc.run([script_path])
    finally:
        if script_path:
            Path(script_path).unlink()


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

    result = proc.run(["gh", "auth", "login", "-s", "codespace"], pass_stdin=True)
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
        logger.error("Failed to list GitHub Codespaces")
        return []

    return [line.split("\t")[0] for line in result.output.splitlines()]


@click.group("codespace")
def codespace_group() -> None:
    _install_gh()


@codespace_group.command("start")
def start_localnet() -> None:
    """Start the AlgoKit LocalNet in a GitHub Codespace."""
    if not _perform_gh_login():
        return

    codespaces = _list_gh_codespaces()

    # Delete existing codespaces with the default name
    for codespace in filter(lambda cs: cs.startswith(DEFAULT_NAME), codespaces):
        proc.run(["gh", "codespace", "delete", "--codespace", codespace, "--force"], pass_stdin=True)

    # Create a new codespace
    codespace_name = f"{DEFAULT_NAME}_{int(time.time())}"
    proc.run(
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
                continue

            if status_result.exit_code == 0 and codespace_data and codespace_data["state"] == "Available":
                codespace_ready = True
                logger.info(f"Codespace {codespace_name} is now ready.")
                logger.warning(
                    "Keep the tab open during the LocalNet session. "
                    "Terminating the session will delete the codespace instance."
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
                    pass_stdin=True,
                )

        logger.info("LocalNet started in GitHub Codespace")
    except KeyboardInterrupt:
        logger.warning("Terminating in progress...")
        if codespace_data:
            logger.warning("Deleting the codespace...")
            proc.run(
                ["gh", "codespace", "delete", "--codespace", codespace_data["name"], "--force"],
                pass_stdin=True,
            )
    finally:
        logger.info("Exiting...")
