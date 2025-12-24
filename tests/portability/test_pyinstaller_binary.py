import logging
import os
import shutil
import subprocess
import sys
import time
from os import environ
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.pyinstaller_binary_tests


def _get_algokit_binary() -> str:
    """Get the path to the algokit binary, preferring the PyInstaller binary over venv-installed version.

    When running via 'poetry run', the .venv/bin directory is prepended to PATH, which causes
    the venv-installed algokit to be found before the PyInstaller binary. This function
    explicitly looks for the binary in the dist directory first.
    """
    # Check for explicit binary path from environment variable
    if binary_path := environ.get("PYINSTALLER_BINARY_PATH"):
        return binary_path

    # Look for the binary in the dist directory (relative to the repo root)
    # This works both locally and in CI
    repo_root = Path(__file__).parent.parent.parent
    is_windows = sys.platform in ("win32", "cygwin")
    binary_name = "algokit.exe" if is_windows else "algokit"
    dist_binary = repo_root / "dist" / "algokit" / binary_name
    if dist_binary.exists():
        return str(dist_binary)

    # Fall back to PATH resolution, but skip the venv bin directory
    # to avoid finding the venv-installed version
    venv_subdir = "Scripts" if is_windows else "bin"
    venv_bin = repo_root / ".venv" / venv_subdir
    original_path = environ.get("PATH", "")
    filtered_path = os.pathsep.join(p for p in original_path.split(os.pathsep) if not p.startswith(str(venv_bin)))

    # Use shutil.which with the filtered PATH
    if binary := shutil.which("algokit", path=filtered_path):
        return binary

    # Last resort: just use 'algokit' and hope it's in PATH
    return "algokit"


algokit = _get_algokit_binary()


@pytest.mark.parametrize(
    ("args", "exit_codes"),
    [
        (["--help"], [0]),
        (["doctor"], [0]),
        (["task", "vanity-address", "PY"], [0]),
    ],
)
def test_non_interactive_algokit_commands(
    args: list[str], exit_codes: list[int], tmp_path_factory: pytest.TempPathFactory
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    # Create a 'playground' directory
    if "build" in args:
        cwd = cwd / "playground"
        cwd.mkdir(exist_ok=True)

    command = [algokit, *args]
    execution_result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=cwd)
    logger.info(f"Command {command} returned {execution_result.stdout}")

    # Parts of doctor will fail in CI on macOS and windows on github actions since docker isn't available by default
    if "doctor" in args and sys.platform in ["darwin", "windows", "win32"] and environ.get("CI"):
        exit_codes.append(1)

    assert execution_result.returncode in exit_codes, f"Command {command} failed with {execution_result.stderr}"


def test_algokit_init_and_project_run(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    # Run algokit init
    init_command = [algokit, "init", "--name", "playground", "-t", "python", "--no-git", "--no-ide", "--defaults"]
    init_result = subprocess.run(init_command, capture_output=True, text=True, check=False, cwd=cwd)
    logger.info(f"Command {init_command} returned {init_result.stdout}")
    assert init_result.returncode == 0, f"Init command failed with {init_result.stderr}"

    # Run algokit project run build
    build_cwd = cwd / "playground"
    build_cwd.mkdir(exist_ok=True)
    build_command = [algokit, "-v", "project", "run", "build", "--", "hello_world"]
    build_result = subprocess.run(build_command, capture_output=True, text=True, check=False, cwd=build_cwd)
    logger.info(f"Command {build_command} returned {build_result.stdout}")
    assert build_result.returncode == 0, f"Build command failed with {build_result.stderr}"


def test_algokit_init_with_template_url(
    dummy_algokit_template_with_python_task: dict[str, Path],
) -> None:
    # TODO: revisit to improve
    # currently we are passing non default option --no-workspace to avoid creating a workspace since its a dummy
    # template. To cover and test workspace creation on real templates, we need to find a way to have `algokit`
    # available globally within the worker running the binary IF the template defined custom copier tasks that invoke
    # global `algokit` executable as part of instantiation of child template (for example fullstack).
    args = [
        "init",
        "--name",
        "testproject",
        "--UNSAFE-SECURITY-accept-template-url",
        "--template-url",
        str(dummy_algokit_template_with_python_task["template_path"]),
        "--template-url-ref=HEAD",
        "--no-git",
        "--no-ide",
        "--defaults",
        "--no-workspace",
    ]

    process = subprocess.Popen(
        [algokit, *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=dummy_algokit_template_with_python_task["cwd"],
    )

    full_output = ""
    logger.info(f"Running command: {' '.join([algokit, *args])}")
    while process.poll() is None and process.stdout and process.stdin:
        output = process.stdout.readline()
        full_output += output  # Accumulate the output
        logger.debug(output.strip())  # Log each line of stdout in real-time

        if "y/n" in output.lower():  # adjust this as needed based on the exact prompt text
            answer = "y\n"
            process.stdin.write(answer)
            process.stdin.flush()

        time.sleep(0.1)

    # After the process ends, log the full stdout
    logger.info(f"Command init returned:\n{full_output}")
    logger.error(process.stderr)
    assert process.returncode == 0, f"Command init failed with {process.stderr}"
