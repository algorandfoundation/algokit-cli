import os
import platform
import re
import shutil
import socket
import sys
import threading
import time
from collections.abc import Callable, Iterator
from itertools import cycle
from os import environ
from pathlib import Path
from shutil import which
from typing import Any

import click
import dotenv

from algokit.core import proc

CLEAR_LINE = "\033[K"
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# From _WIN_DEFAULT_PATHEXT from shutils
WIN_DEFAULT_PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC"


def extract_version_triple(version_str: str) -> str:
    match = re.search(r"\d+\.\d+\.\d+", version_str)
    if not match:
        raise ValueError("Unable to parse version number")
    return match.group()


def is_minimum_version(system_version: str, minimum_version: str) -> bool:
    system_version_as_tuple = tuple(map(int, system_version.split(".")))
    minimum_version_as_tuple = tuple(map(int, minimum_version.split(".")))
    return system_version_as_tuple >= minimum_version_as_tuple


def is_network_available(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """
    Check if internet is available by trying to establish a socket connection.
    """

    try:
        socket.setdefaulttimeout(timeout)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def animate(name: str, stop_event: threading.Event) -> None:
    """Displays an animated spinner in the console."""
    # Ensure sys.stdout uses UTF-8 encoding
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)  # noqa: SIM115, PTH123

    for frame in cycle(SPINNER_FRAMES):
        if stop_event.is_set():
            break
        text = f"\r{frame} {name}"
        sys.stdout.write(text)
        sys.stdout.flush()
        time.sleep(0.1)

    sys.stdout.write("\r" + CLEAR_LINE)  # Clear the animation line
    sys.stdout.flush()


def run_with_animation(
    target_function: Callable[..., Any], animation_text: str = "Loading", *args: Any, **kwargs: Any
) -> Any:  # noqa: ANN401
    """Executes a function while displaying an animation, handling termination."""
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate, args=(animation_text, stop_event), daemon=True)
    animation_thread.start()

    try:
        result: Any = target_function(*args, **kwargs)
    except Exception:
        raise  # Re-raise to propagate the exception
    finally:
        stop_event.set()
        animation_thread.join()  # Wait for animation to finish

    return result


def find_valid_pipx_command(error_message: str) -> list[str]:
    for pipx_command in get_candidate_pipx_commands():
        try:
            pipx_version_result = proc.run([*pipx_command, "--version"])
        except OSError:
            pass  # in case of path/permission issues, go to next candidate
        else:
            if pipx_version_result.exit_code == 0:
                return pipx_command
    # If pipx isn't found in global path or python -m pipx then bail out
    #   this is an exceptional circumstance since pipx should always be present with algokit
    #   since it's installed with brew / winget as a dependency, and otherwise is used to install algokit
    raise click.ClickException(error_message)


def get_candidate_pipx_commands() -> Iterator[list[str]]:
    # first try is pipx via PATH
    yield ["pipx"]
    # otherwise try getting an interpreter with pipx installed as a module,
    # this won't work if pipx is installed in its own venv but worth a shot
    for python_path in get_python_paths():
        yield [python_path, "-m", "pipx"]


def get_npm_command(error_message: str, *, is_npx: bool = False) -> list[str]:
    command = "npx" if is_npx else "npm"
    path = shutil.which(command)
    if not path:
        raise click.ClickException(error_message)
        # Create the npm directory inside %APPDATA% if it doesn't exist, as npx on windows needs this.
        # See https://github.com/npm/cli/issues/7089 for more details.
    if is_windows():
        appdata_dir = os.getenv("APPDATA")
        if appdata_dir is not None:
            appdata_dir_path = Path(appdata_dir).expanduser()
            npm_dir = appdata_dir_path / "npm"
            try:
                if not npm_dir.exists():
                    npm_dir.mkdir(parents=True)
            except OSError as ex:
                raise click.ClickException(
                    f"Failed to create the `npm` directory in {appdata_dir_path}.\n"
                    "This command uses `npx`, which requires the `npm` directory to exist "
                    "in the above path, otherwise an ENOENT 4058 error will occur.\n"
                    "Please create this directory manually and try again."
                ) from ex
        return [f"{command}.cmd"]
    return [command]


def get_python_paths() -> Iterator[str]:
    for python_name in ("python3", "python"):
        if python_path := which(python_name):
            yield python_path
    python_base_path = get_base_python_path()
    if python_base_path is not None:
        yield python_base_path


def get_base_python_path() -> str | None:
    this_python: str | None = sys.executable
    if not this_python or this_python.endswith("algokit"):
        # Not: can be empty or None... yikes! unlikely though
        # https://docs.python.org/3.10/library/sys.html#sys.executable
        return None
    # not in venv... not recommended to install algokit this way, but okay
    if sys.prefix == sys.base_prefix:
        return this_python
    this_python_path = Path(this_python)
    # try resolving symlink, this should be default on *nix
    try:
        if this_python_path.is_symlink():
            return str(this_python_path.resolve())
    except (OSError, RuntimeError):
        pass
    # otherwise, try getting an internal value which should be set when running in a .venv
    # this will be the value of `home = <path>` in pyvenv.cfg if it exists
    if base_home := getattr(sys, "_home", None):
        base_home_path = Path(base_home)
        for name in ("python", "python3", f"python3.{sys.version_info.minor}"):
            candidate_path = base_home_path / name
            if is_windows():
                candidate_path = candidate_path.with_suffix(".exe")
            if candidate_path.is_file():
                return str(candidate_path)
    # give up, we tried...
    return this_python


def is_binary_mode() -> bool:
    """
    Check if the current Python interpreter is running in a native binary frozen environment.
    return: True if running in a native binary frozen environment, False otherwise.
    """
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_wsl() -> bool:
    """
    detects if Python is running in WSL
    https://github.com/scivision/detect-windows-subsystem-for-linux
    """
    return platform.uname().release.endswith(("-Microsoft", "microsoft-standard-WSL2"))


def split_command_string(command: str) -> list[str]:
    """
    Parses a command string into a list of arguments, handling both shell and non-shell commands
    """

    if platform.system() == "Windows":
        import mslex

        return mslex.split(command)
    else:
        import shlex

        return shlex.split(command)


def resolve_command_path(
    command: list[str],
) -> list[str]:
    """
    Encapsulates custom command resolution, promotes reusability

    Args:
        command (list[str]): The command to resolve
        allow_chained_commands (bool): Whether to allow chained commands (e.g. "&&" or "||")

    Returns:
        list[str]: The resolved command
    """

    cmd, *args = command

    # No resolution needed if the command already has a path or is not Windows-specific
    if Path(cmd).name != cmd:
        return command

    # Windows-specific handling if 'shutil.which' fails:
    if is_windows():
        for ext in environ.get("PATHEXT", WIN_DEFAULT_PATHEXT).split(";"):
            potential_path = shutil.which(cmd + ext)
            if potential_path:
                return [potential_path, *args]

    # If resolves directly, return
    if resolved_cmd := shutil.which(cmd):
        return [resolved_cmd, *args]

    # Command not found with any extension
    raise click.ClickException(f"Failed to resolve command path, '{cmd}' wasn't found")


def load_env_file(path: Path) -> dict[str, str | None]:
    """Load the general .env configuration.

    Args:
        path (Path): Path to the .env file or directory containing the .env file.

    Returns:
        dict[str, str | None]: Dictionary with .env configurations.
    """

    # Check if the path is a file, if yes, use it directly
    if path.is_file():
        env_path = path
    else:
        # Assume the default .env file name in the given directory
        env_path = path / ".env"

    if env_path.exists():
        return dotenv.dotenv_values(env_path, verbose=True)
    return {}


def alphanumeric_sort_key(s: str) -> list[int | str]:
    """
    Generate a key for sorting strings that contain both text and numbers.
    For instance, ensures that "name_digit_1" comes before "name_digit_2".
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split("([0-9]+)", s)]
