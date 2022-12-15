import dataclasses
import json
import logging
import platform
import shutil
from datetime import datetime, timezone
from sys import version_info as sys_version_info

from algokit.core import proc
from algokit.core.proc import RunResult

logger = logging.getLogger(__name__)

DOCKER_COMPOSE_MINIMUM_VERSION = "2.5.0"

DOCKER_COMPOSE_MINIMUM_VERSION_MESSAGE = (
    f"\nDocker Compose {DOCKER_COMPOSE_MINIMUM_VERSION} required to `run algokit sandbox command`; "
    "install via https://docs.docker.com/compose/install/"
)


@dataclasses.dataclass
class ProcessResult:
    info: str
    exit_code: int


def get_date() -> ProcessResult:
    return ProcessResult(format(datetime.now(timezone.utc).isoformat()), 0)


def get_algokit_info() -> ProcessResult:
    try:
        pipx_list_process_results = proc.run(["pipx", "list", "--short"])
        algokit_pipx_line = [
            line for line in pipx_list_process_results.output.splitlines() if line.startswith("algokit")
        ]
        algokit_version = algokit_pipx_line[0].split(" ")[1]

        algokit_location = ""
        pipx_env_process_results = proc.run(["pipx", "environment"])
        algokit_pip_line = [
            line for line in pipx_env_process_results.output.splitlines() if line.startswith("PIPX_LOCAL_VENVS")
        ]
        pipx_venv_location = algokit_pip_line[0].split("=")[1]
        algokit_location = f"{pipx_venv_location}/algokit"
        return ProcessResult(f"{algokit_version} {algokit_location}", 0)
    except Exception:
        return ProcessResult("None found", 1)


def get_choco_info() -> ProcessResult:
    try:
        process_results = proc.run(["choco"])
        return ProcessResult(process_results.output.splitlines()[0].split(" v")[1], process_results.exit_code)
    except Exception:
        return ProcessResult("None found", 1)


def get_brew_info() -> ProcessResult:
    try:
        process_results = proc.run(["brew", "-v"])
        return ProcessResult(process_results.output.splitlines()[0].split(" ")[1], process_results.exit_code)
    except Exception:
        return ProcessResult("None found", 1)


def get_os(os_type: str) -> ProcessResult:
    os_version = ""
    os_name = ""
    if os_type == "windows":
        os_name = "Windows"
        os_version = platform.win32_ver()[0]
    elif os_type == "darwin":
        os_name = "Mac OS X"
        os_version = platform.mac_ver()[0]
    else:
        os_name = "Unix/Linux"
        os_version = platform.version()
    return ProcessResult(f"{os_name} {os_version}", 0)


def get_docker_info() -> ProcessResult:
    try:
        process_results = proc.run(["docker", "-v"])
        return ProcessResult(
            process_results.output.splitlines()[0].split(" ")[2].split(",")[0], process_results.exit_code
        )
    except Exception:
        return ProcessResult(
            (
                "None found.\nDocker required to `run algokit sandbox` command;"
                " install via https://docs.docker.com/get-docker/"
            ),
            1,
        )


def get_docker_compose_info() -> ProcessResult:
    try:

        process_results = get_docker_compose_version("")
        compose_version: dict[str, str] = json.loads(process_results.output)
        compose_version_str = compose_version["version"].lstrip("v")
        compose_minimum_version_met = is_minimum_version(compose_version_str, DOCKER_COMPOSE_MINIMUM_VERSION)

        # docker_compose_version = process_results.output.splitlines()[0].split(" v")[2]
        # minimum_version_met = is_minimum_version(docker_compose_version, DOCKER_COMPOSE_MINIMUM_VERSION)

        return ProcessResult(
            (
                compose_version_str
                if compose_minimum_version_met
                else f"{compose_version_str}{DOCKER_COMPOSE_MINIMUM_VERSION_MESSAGE}"
            ),
            process_results.exit_code if compose_minimum_version_met else 1,
        )
    except Exception:
        return ProcessResult(f"None found. {DOCKER_COMPOSE_MINIMUM_VERSION_MESSAGE}", 1)


def get_git_info(system: str) -> ProcessResult:
    try:
        process_results = proc.run(["git", "-v"])
        return ProcessResult(process_results.output.splitlines()[0].split(" ")[2], process_results.exit_code)
    except Exception:
        if system == "windows":
            return ProcessResult(
                (
                    "None found.\nGit required to `run algokit init`; install via `choco install git` "
                    "if using Chocolatey or via https://github.com/git-guides/install-git#install-git-on-windows"
                ),
                1,
            )
        else:
            return ProcessResult(
                "None found.\nGit required to run `algokit init`; "
                "install via https://github.com/git-guides/install-git",
                1,
            )


def get_algokit_python_info() -> ProcessResult:
    try:
        return ProcessResult(f"{sys_version_info.major}.{sys_version_info.minor}.{sys_version_info.micro}", 0)
    except Exception:
        return ProcessResult("None found.", 1)


def get_global_python_info() -> ProcessResult:
    try:
        global_python3_version = proc.run(["python3", "--version"]).output.splitlines()[0].split(" ")[1]
        global_python3_location = shutil.which("python3")
        return ProcessResult(f"{global_python3_version} {global_python3_location}", 0)
    except Exception:
        return ProcessResult("None found.", 1)


def get_pipx_info() -> ProcessResult:
    try:
        process_results = proc.run(["pipx", "--version"])
        return ProcessResult(process_results.output.splitlines()[0], process_results.exit_code)
    except Exception:
        return ProcessResult(
            "None found.\nPipx is required to install Poetry; install via https://pypa.github.io/pipx/", 1
        )


def get_poetry_info() -> ProcessResult:
    try:
        process_results = proc.run(["poetry", "--version"])
        poetry_version = process_results.output.splitlines()[-1].split("version ")[1].split(")")[0]
        return ProcessResult(poetry_version, process_results.exit_code)
    except Exception:
        return ProcessResult(
            (
                "None found.\nPoetry is required for some Python-based templates; install via `algokit bootstrap` "
                "within project directory, or via https://python-poetry.org/docs/#installation"
            ),
            1,
        )


def get_node_info() -> ProcessResult:
    try:
        process_results = proc.run(["node", "-v"])
        return ProcessResult(process_results.output.splitlines()[0].split("v")[1], process_results.exit_code)
    except Exception:
        return ProcessResult(
            (
                "None found.\nNode.js is required for some Node.js-based templates; install via `algokit bootstrap` "
                "within project directory, or via https://nodejs.dev/en/learn/how-to-install-nodejs/"
            ),
            1,
        )


def get_npm_info() -> ProcessResult:
    try:
        process_results = proc.run(["npm", "-v"])
        return ProcessResult(process_results.output.splitlines()[0], process_results.exit_code)
    except Exception:
        return ProcessResult("None found.", 1)


def is_minimum_version(current_version: str, minimum_version: str) -> bool:
    system_version_as_tuple = tuple(map(int, (current_version.split("."))))
    minimum_version_as_tuple = tuple(map(int, (minimum_version.split("."))))
    return system_version_as_tuple >= minimum_version_as_tuple


def get_docker_compose_version(bad_return_code_error_message: str) -> RunResult:
    return proc.run(
        ["docker", "compose", "version", "--format", "json"],
        bad_return_code_error_message=bad_return_code_error_message,
    )
