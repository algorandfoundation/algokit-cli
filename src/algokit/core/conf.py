import os
import platform
from functools import cache
from pathlib import Path

PACKAGE_NAME = "algokit"


@cache
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


@cache
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
    return result


def read_config(file_name: str):
    """Read a file from config (things that should persist, and potentially follow a user)"""
    return (get_app_config_dir() / file_name).read_text()


def read_state(file_name: str):
    """Read a file from state (things the user wouldn't normally interact with directly)"""
    return (get_app_state_dir() / file_name).read_text()


def write_config(file_name: str, content: str):
    """Write a file to config (things that should persist, and potentially follow a user)"""
    config_file = get_app_config_dir() / file_name
    config_file.write_text(content)


def write_state(file_name: str, content: str):
    """Write a file to state (things the user wouldn't normally interact with directly)"""
    config_file = get_app_state_dir() / file_name
    config_file.write_text(content)
