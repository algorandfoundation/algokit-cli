import logging
import os
import platform
import sys
from importlib import metadata
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from algokit.core.constants import ALGOKIT_CONFIG

PACKAGE_NAME = "algokit"

logger = logging.getLogger(__name__)


def get_app_config_dir() -> Path:
    """Get the application config files location - things that should persist, and potentially follow a user"""
    os_type = platform.system().lower()
    if os_type == "windows":
        config_dir = os.getenv("APPDATA")
    else:
        config_dir = os.getenv("XDG_CONFIG_HOME")
    if config_dir is None:
        config_dir = "~/.config"
    return _get_relative_app_path(config_dir)


def get_app_state_dir() -> Path:
    """Get the application state files location - things the user wouldn't normally interact with directly"""
    os_type = platform.system().lower()
    if os_type == "windows":
        state_dir = os.getenv("LOCALAPPDATA")
    elif os_type == "darwin":
        state_dir = "~/Library/Application Support"
    else:
        state_dir = os.getenv("XDG_STATE_HOME")
    if state_dir is None:
        state_dir = "~/.local/state"
    return _get_relative_app_path(state_dir)


def _get_relative_app_path(base_dir: str) -> Path:
    path = Path(base_dir).expanduser()
    result = path / PACKAGE_NAME
    result.mkdir(parents=True, exist_ok=True)
    # resolve path in case of UWP sandbox redirection
    return result.resolve()


def get_current_package_version() -> str:
    return metadata.version(PACKAGE_NAME)


def get_algokit_config(project_dir: Path, config_filename: str = ALGOKIT_CONFIG) -> dict | None:
    """
    Load and parse a TOML configuration file.
    :param project_dir: Project directory path.
    :param config_filename: Configuration filename.
    :return: A dictionary containing the configuration or None if not found.
    """
    try:
        config_path = project_dir / config_filename
        config_text = config_path.read_text("utf-8")
    except FileNotFoundError:
        logger.debug(f"No {config_filename} file found in the project directory.")
        return None
    except Exception as ex:
        logger.debug(f"Unexpected error reading {config_filename} file: {ex}")
        return None

    try:
        return tomllib.loads(config_text)
    except Exception as ex:
        logger.debug(f"Error parsing {config_filename} file: {ex}")
        return None
