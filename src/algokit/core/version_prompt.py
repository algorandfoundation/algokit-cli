import logging
import os
import re
from datetime import timedelta
from importlib import metadata
from time import time

import click
import httpx
from algokit.core.conf import PACKAGE_NAME, get_app_config_dir, get_app_state_dir

logger = logging.getLogger(__name__)
Version = None | tuple[int, int, int]  #  type: ignore[misc]

LATEST_URL = "https://api.github.com/repos/algorandfoundation/algokit-cli/releases/latest"
VERSION_CHECK_INTERVAL = timedelta(weeks=1).total_seconds()


def do_version_prompt() -> None:
    if _is_version_prompt_disabled():
        logger.debug("Version prompt disabled")
        return

    current_version = get_current_version()
    if current_version is None:
        logger.debug("Could not determine current version")
        return

    latest_version = get_latest_version_or_cached()
    if latest_version is None:
        logger.debug("Could not determine latest version")
        return

    if current_version < latest_version:
        logger.info(
            f"You are using AlgoKit version {format_version(current_version)}, "
            f"however version {format_version(latest_version)} is available."
        )
    else:
        logger.debug("Current version is up to date")


def format_version(version: Version) -> str:
    return "" if version is None else ".".join(map(str, version))


def _parse_version(version_str: str) -> Version:
    if version_str:
        version_int = tuple(map(int, version_str.split(".")))
        if len(version_int) == 3:
            return version_int  # type: ignore[return-value]
    return None


def get_latest_version_or_cached() -> Version:
    version_check_path = get_app_state_dir() / "last-version-check"

    version: Version = None
    last_checked = None
    try:
        last_checked = version_check_path.stat().st_mtime
        version = _parse_version(version_check_path.read_text(encoding="utf-8"))
        logger.debug(f"{version} found in cache {version_check_path}")
    except FileNotFoundError:
        logger.debug(f"{version_check_path} not found")
    except Exception as ex:
        logger.debug(f"Unexpected error parsing {version_check_path}", exc_info=ex)

    now = time()
    if last_checked is None or (now - last_checked) > VERSION_CHECK_INTERVAL:
        version = get_latest_version()
        last_checked = now
        version_check_path.write_text(format_version(version), encoding="utf-8")
    return version


def get_current_version() -> Version:
    return _parse_version(metadata.version(PACKAGE_NAME))


def get_latest_version() -> Version:
    headers = {"ACCEPT": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    # TODO: remove GH_TOKEN auth once algokit repo is public
    gh_token = os.getenv("GH_TOKEN")
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    response = httpx.get(LATEST_URL, headers=headers)
    if response.status_code != 200:
        return None

    json = response.json()
    tag_name: str = json["tag_name"]
    logger.debug(f"Latest version tag: {tag_name}")
    match = re.match(r"v(\d+\.\d+\.\d+)", tag_name)
    if not match:
        return None
    return tuple(map(int, match.group(1).split(".")))  # type: ignore[return-value]


def _is_version_prompt_disabled() -> bool:
    disable_marker = get_app_config_dir() / "disable-version-prompt"
    return disable_marker.exists()


skip_version_check_option = click.option(
    "--skip-version-check",
    is_flag=True,
    show_default=False,
    default=False,
    help="Skip version checking and prompting.",
)


@click.command("version-prompt", short_help="Enables or disables version prompt")
@click.argument("enable", required=False, type=bool, default=None)
def version_prompt_configuration_command(*, enable: bool | None) -> None:
    if enable is not None:
        disable_marker = get_app_config_dir() / "disable-version-prompt"
        if enable:
            disable_marker.unlink(missing_ok=True)
            logger.info("📡 Resuming check for new versions")
        else:
            disable_marker.touch()
            logger.info("🚫 Will stop checking for new versions")
    else:
        logger.info(str(not _is_version_prompt_disabled()))
