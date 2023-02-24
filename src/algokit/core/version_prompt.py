import logging
import os
import re
from datetime import timedelta
from time import time

import click
import httpx

from algokit.core.conf import get_app_config_dir, get_app_state_dir, get_current_package_version

logger = logging.getLogger(__name__)

LATEST_URL = "https://api.github.com/repos/algorandfoundation/algokit-cli/releases/latest"
VERSION_CHECK_INTERVAL = timedelta(weeks=1).total_seconds()
DISABLE_CHECK_MARKER = "disable-version-prompt"


def do_version_prompt() -> None:
    if _skip_version_prompt():
        logger.debug("Version prompt disabled")
        return

    current_version = get_current_package_version()
    latest_version = get_latest_version_or_cached()
    if latest_version is None:
        logger.debug("Could not determine latest version")
        return

    if _get_version_sequence(current_version) < _get_version_sequence(latest_version):
        logger.info(f"You are using AlgoKit version {current_version}, however version {latest_version} is available.")
    else:
        logger.debug("Current version is up to date")


def _get_version_sequence(version: str) -> list[int | str]:
    match = re.match(r"(\d+)\.(\d+)\.(\d+)(.*)", version)
    if match:
        return [int(x) for x in match.groups()[:3]] + [match.group(4)]
    return [version]


def get_latest_version_or_cached() -> str | None:
    version_check_path = get_app_state_dir() / "last-version-check"

    try:
        last_checked = os.path.getmtime(version_check_path)
        version = version_check_path.read_text(encoding="utf-8")
    except OSError:
        logger.debug(f"{version_check_path} inaccessible")
        last_checked = 0
        version = None
    else:
        logger.debug(f"{version} found in cache {version_check_path}")

    if (time() - last_checked) > VERSION_CHECK_INTERVAL:
        try:
            version = get_latest_github_version()
        except Exception as ex:
            logger.debug("Checking for latest version failed", exc_info=ex)
            # update last checked time even if check failed
            version_check_path.touch()
        else:
            version_check_path.write_text(version, encoding="utf-8")
    # handle case where the first check failed, so we have an empty file
    return version or None


def get_latest_github_version() -> str:
    headers = {"ACCEPT": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

    response = httpx.get(LATEST_URL, headers=headers)
    response.raise_for_status()

    json = response.json()
    tag_name = json["tag_name"]
    logger.debug(f"Latest version tag: {tag_name}")
    match = re.match(r"v(\d+\.\d+\.\d+)", tag_name)
    if not match:
        raise ValueError(f"Unable to extract version from tag_name: {tag_name}")
    return match.group(1)


def _skip_version_prompt() -> bool:
    disable_marker = get_app_config_dir() / DISABLE_CHECK_MARKER
    return disable_marker.exists()


skip_version_check_option = click.option(
    "--skip-version-check",
    is_flag=True,
    show_default=False,
    default=False,
    help="Skip version checking and prompting.",
)


@click.command(
    "version-prompt", short_help="Enables or disables checking and prompting if a new version of AlgoKit is available"
)
@click.argument("enable", required=False, type=click.Choice(["enable", "disable"]), default=None)
def version_prompt_configuration_command(*, enable: str | None) -> None:
    """Controls whether AlgoKit checks and prompts for new versions.
    Set to [disable] to prevent AlgoKit performing this check permanently, or [enable] to resume checking.
    If no argument is provided then outputs current setting.

    Also see --skip-version-check which can be used to disable check for a single command."""
    if enable is None:
        logger.info("disable" if _skip_version_prompt() else "enable")
    else:
        disable_marker = get_app_config_dir() / DISABLE_CHECK_MARKER
        if enable == "enable":
            disable_marker.unlink(missing_ok=True)
            logger.info("📡 Resuming check for new versions")
        else:
            disable_marker.touch()
            logger.info("🚫 Will stop checking for new versions")
