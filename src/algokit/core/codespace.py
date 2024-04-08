import json
import logging
import subprocess
import tempfile
import time
from functools import cache
from pathlib import Path
from typing import Any

import httpx

from algokit.core import proc, questionary_extensions
from algokit.core.utils import is_windows, run_with_animation

logger = logging.getLogger(__name__)

GH_WEBI_INSTALLER_URL = "https://webi.sh/gh"
CODESPACE_PORT_FORWARD_RETRY_SECONDS = 5
CODESPACE_NAME_PREFIX = "algokit-localnet"
CODESPACE_CREATE_TIMEOUT = 60
CODESPACE_CREATE_RETRY_TIMEOUT = 10
CODESPACE_CONTAINER_AVAILABLE = "Available"
CODESPACE_TOO_MANY_ERROR_MSG = "too many codespaces"
CODESPACE_LOADING_MSG = "Provisioning a new codespace instance..."


def _try_forward_ports_once(ports: list[tuple[int, int]], codespace_name: str, log_level: int = logging.INFO) -> bool:
    command = [
        "gh",
        "codespace",
        "ports",
        "forward",
        "--codespace",
        codespace_name,
        *(f"{external_port}:{internal_port}" for internal_port, external_port in ports),
    ]

    try:
        response = proc.run(command, pass_stdin=True, stdout_log_level=log_level)
        return response.exit_code == 0
    except Exception as e:
        logger.error(f"Port forwarding attempt failed with error: {e}")
        return False


def ensure_github_cli_installed() -> None:
    """
    Ensures GitHub CLI (`gh`) is installed, installing it if necessary.
    """
    try:
        proc.run(["gh", "--version"])
    except Exception:
        logger.info("Installing gh...")
        try:
            if is_windows():
                proc.run(["winget", "install", "--id", "GitHub.cli", "--silent"])
            else:
                install_github_cli_via_webi()
        except Exception as e:
            logger.error(f"Failed to automatically install gh cli: {e}")
            logger.error(
                "Please install `gh cli` manually by following official documentation at https://cli.github.com/"
            )
            raise
        logger.info("gh installed successfully!")


def install_github_cli_via_webi() -> None:
    """
    Installs `gh` using the `webi.sh` script.
    """
    response = httpx.get(GH_WEBI_INSTALLER_URL)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=True, mode="w") as tmp_file:
        tmp_file.write(response.text)
        script_path = tmp_file.name
        Path(script_path).chmod(0o755)
        proc.run([script_path])


@cache
def is_github_cli_authenticated() -> bool:
    """
    Checks if the user is authenticated with GitHub CLI and has the 'codespace' scope.
    """
    try:
        result = proc.run(["gh", "auth", "status"])

        # Normalize output for easier parsing
        normalized_output = " ".join(result.output.splitlines()).lower()

        # Check for authentication and 'codespace' scope
        authenticated = "logged in" in normalized_output
        has_codespace_scope = "codespace" in normalized_output

        if not authenticated:
            logger.error("GitHub CLI authentication check failed. Please login with `gh auth login -s codespace`.")
        if not has_codespace_scope:
            logger.error(
                "Required 'codespace' scope is missing. "
                "Please ensure you have the 'codespace' scope by running "
                "`gh auth refresh-token -s codespace`."
            )

        return authenticated and has_codespace_scope
    except subprocess.CalledProcessError:
        logger.error("GitHub CLI authentication check failed. Please login with `gh auth login -s codespace`.")
        return False


def authenticate_with_github() -> bool:
    """
    Logs the user into GitHub Codespace.
    """
    if is_github_cli_authenticated():
        return True

    result = proc.run_interactive(
        ["gh", "auth", "login", "-s", "codespace"],
    )
    if result.exit_code != 0:
        logger.error("Failed to start LocalNet in GitHub Codespace")
        return False
    logger.info("Logged in to GitHub Codespace")
    return True


def list_github_codespaces() -> list[str]:
    """
    Lists available GitHub Codespaces.
    """
    if not is_github_cli_authenticated():
        return []

    result = proc.run(["gh", "codespace", "list"], pass_stdin=True)

    if result.exit_code != 0:
        logger.error("Failed to log in to GitHub Codespaces. Run with -v flag for more details.")
        logger.debug(result.output, result.exit_code)
        return []

    return [line.split("\t")[0] for line in result.output.splitlines()]


def forward_ports_for_codespace(
    codespace_name: str, algod_port: int, kmd_port: int, indexer_port: int, max_retries: int = 5
) -> None:
    """
    Forwards specified ports for a GitHub Codespace with retries.
    """
    ports = [
        (algod_port, 4001),
        (kmd_port, 4002),
        (indexer_port, 8980),
    ]

    for attempt in reversed(range(1, max_retries + 1)):
        if _try_forward_ports_once(ports, codespace_name):
            logger.info("Port forwarding successful.")
            break
        logger.error("Port forwarding failed!")
        if attempt > 1:
            run_with_animation(
                time.sleep, f"Retrying ({attempt - 1} attempts left)...", CODESPACE_PORT_FORWARD_RETRY_SECONDS
            )
    else:
        raise Exception("All port forwarding attempts failed.")


def delete_codespaces_with_prefix(codespaces: list[str], default_name: str) -> None:
    """
    Deletes GitHub Codespaces that start with the specified default name.

    Args:
        codespaces (list[str]): List of codespace names.
        default_name (str): The prefix to match for deletion.
    """
    for codespace in filter(lambda cs: cs.startswith(default_name), codespaces):
        proc.run(["gh", "codespace", "delete", "--codespace", codespace, "--force"], pass_stdin=True)
        logger.info(f"Deleted unused codespace {codespace}")


def is_codespace_ready(codespace_name: str) -> dict[str, Any]:
    """
    Checks if the specified codespace is ready.

    Args:
        codespace_name (str): The name of the codespace to check.

    Returns:
        dict[str, Any] | None: The codespace data if ready, None otherwise.
    """
    max_retries = 10
    while max_retries > 0:
        max_retries -= 1

        status_result = proc.run(
            ["gh", "codespace", "list", "--json", "displayName", "--json", "state", "--json", "name"],
            pass_stdin=True,
        )
        try:
            codespace_data: dict[str, Any] = next(
                data for data in json.loads(status_result.output.strip()) if data["displayName"] == codespace_name
            )
        except StopIteration:
            run_with_animation(
                time.sleep,
                CODESPACE_LOADING_MSG,
                CODESPACE_CREATE_RETRY_TIMEOUT,
            )
            continue

        if status_result.exit_code == 0 and codespace_data and codespace_data["state"] == CODESPACE_CONTAINER_AVAILABLE:
            return codespace_data
    raise RuntimeError(
        "After 10 attempts, codespace isn't ready. Avoid codespace deletion and retry with --codespace-name."
    )


def delete_codespace(*, codespace_data: dict[str, Any], force: bool) -> None:
    """
    Deletes the specified codespace.

    Args:
        codespace_data (dict[str, Any]): The codespace data.
        force (bool): Whether to force deletion without confirmation.
    """
    if codespace_data and (force or questionary_extensions.prompt_confirm("Delete the codespace?", default=True)):
        logger.warning(f"Deleting the `{codespace_data['name']}` codespace...")
        proc.run(
            ["gh", "codespace", "delete", "--codespace", codespace_data["name"], "--force"],
            pass_stdin=True,
        )


def create_codespace(repo_url: str, codespace_name: str, machine: str) -> None:
    """
    Creates a GitHub Codespace with the specified repository, display name, and machine type.

    Args:
        repo_url (str): The URL of the repository for the codespace.
        codespace_name (str): The display name for the codespace.
        machine (str): The machine type for the codespace.
    """
    response = proc.run(
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
    if response.exit_code != 0 and CODESPACE_TOO_MANY_ERROR_MSG in response.output.lower():
        raise Exception(
            "Creation failed: User's codespace limit reached. Delete unused codespaces using `gh` cli and try again."
        )

    run_with_animation(
        time.sleep,
        CODESPACE_LOADING_MSG,
        CODESPACE_CREATE_TIMEOUT,
    )
