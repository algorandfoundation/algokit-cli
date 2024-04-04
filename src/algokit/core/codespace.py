import logging
import subprocess
import tempfile
import time
from functools import cache
from pathlib import Path

import httpx

from algokit.core import proc
from algokit.core.utils import is_windows

logger = logging.getLogger(__name__)

GH_WEBI_INSTALLER_URL = "https://webi.sh/gh"


def ensure_gh_installed() -> None:
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
                install_gh_via_webi()
        except Exception as e:
            logger.error(f"Failed to automatically install gh cli: {e}")
            logger.error(
                "Please install `gh cli` manually by following official documentation at https://cli.github.com/"
            )
            raise
        logger.info("gh installed successfully!")


def install_gh_via_webi() -> None:
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
def gh_is_authenticated() -> bool:
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


def login_to_gh() -> bool:
    """
    Logs the user into GitHub Codespace.
    """
    if gh_is_authenticated():
        return True

    result = proc.run_interactive(
        ["gh", "auth", "login", "-s", "codespace"],
    )
    if result.exit_code != 0:
        logger.error("Failed to start LocalNet in GitHub Codespace")
        return False
    logger.info("Logged in to GitHub Codespace")
    return True


def get_gh_codespaces_list() -> list[str]:
    """
    Lists available GitHub Codespaces.
    """
    if not gh_is_authenticated():
        return []

    result = proc.run(["gh", "codespace", "list"], pass_stdin=True)

    if result.exit_code != 0:
        logger.error("Failed to log in to GitHub Codespaces. Run with -v flag for more details.")
        logger.debug(result.output, result.exit_code)
        return []

    return [line.split("\t")[0] for line in result.output.splitlines()]


def forward_codespace_ports(
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

    def _try_forward_ports_once() -> proc.RunResult:
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
        result = _try_forward_ports_once()
        if result:
            return
        logger.error("Port forwarding failed!")
        if attempt > 1:
            logger.info(f"Retrying ({attempt - 1} attempts left)...")
            time.sleep(10)

    raise Exception("All port forwarding attempts failed.")
