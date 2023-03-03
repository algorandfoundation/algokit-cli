import os
import platform
from importlib import metadata
from pathlib import Path

PACKAGE_NAME = "algokit"


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
