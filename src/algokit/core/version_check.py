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


@click.pass_context
def do_version_check(context: click.Context, _: None) -> None:
    _do_version_check(context)


# this second function is to allow mocking
def _do_version_check(context: click.Context) -> None:
    if context.obj["skip_version_check"] or _is_version_check_disabled():
        logger.debug("Skipping version check")
        return

    current_version = _parse_version(metadata.version(PACKAGE_NAME))
    if current_version is None:
        logger.debug("Could not determine current version")
        return

    latest_version = get_latest_version_or_cached()
    if latest_version is None:
        logger.debug("Could not determine latest version")
        return

    if current_version < latest_version:
        logger.info(
            f"You are using AlgoKit version {_version_str(current_version)}, "
            f"however version {_version_str(latest_version)} is available."
        )
    else:
        logger.debug("Current version is up to date")


def _version_str(version: Version) -> str:
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
        version_check_path.write_text(_version_str(version), encoding="utf-8")
    return version


def get_latest_version() -> Version:
    headers = {"ACCEPT": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    # while algokit is private we need a token to query the release
    gh_token = os.getenv("GH_TOKEN")
    if gh_token:
        logger.debug("Using GH_TOKEN to query latest version")
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


def _set_version_check(_ctx: click.Context, _: click.Option, value: bool | None) -> None:
    if value is not None:
        _store_version_check(enable=value)
        _ctx.exit()


def _skip_version_check(_ctx: click.Context, _: click.Option, value: bool) -> None:  # noqa FBT001
    _ctx.ensure_object(dict)
    _ctx.obj["skip_version_check"] = value


def _is_version_check_disabled() -> bool:
    disable_marker = get_app_config_dir() / "disable-version-check"
    return disable_marker.exists()


def _store_version_check(*, enable: bool) -> None:
    disable_marker = get_app_config_dir() / "disable-version-check"
    if enable:
        disable_marker.unlink(missing_ok=True)
        logger.info("Version check enabled")
    else:
        disable_marker.touch()
        logger.info("Version check disabled")


version_check_option = click.option(
    "--enable-version-check/--disable-version-check",
    callback=_set_version_check,
    show_default=False,
    default=None,
    expose_value=False,
    help="Enable or disable version checking and reporting permanently.",
)

skip_version_check_option = click.option(
    "--skip-version-check",
    is_flag=True,
    callback=_skip_version_check,
    show_default=False,
    default=False,
    expose_value=False,
    help="Skip version checking and reporting.",
)
