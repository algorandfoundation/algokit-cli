import dataclasses
import logging
import platform
import shutil
from datetime import datetime, timezone
from sys import executable as sys_executable
from sys import version_info as sys_version_info

from algokit.core import proc

logger = logging.getLogger(__name__)

DOCKER_COMPOSE_MINIMUM_VERSION = "2.5"

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
    except Exception as e:
        logger.debug(f"Getting algokit version failed: {e}", exc_info=True)
        return ProcessResult("None found", 1)


def get_choco_info() -> ProcessResult:
    try:
        process_results = proc.run(["choco"]).output.splitlines()[0].split(" v")[1]
        major, minor, build = get_version_from_str(process_results)
        return ProcessResult(f"{major}.{minor}.{build}", 0)
    except Exception as e:
        logger.debug(f"Getting chocolatey version failed: {e}", exc_info=True)
        return ProcessResult("None found", 1)


def get_brew_info() -> ProcessResult:
    try:
        process_results = proc.run(["brew", "-v"]).output.splitlines()[0].split(" ")[1].split("-")[0]
        major, minor, build = get_version_from_str(process_results)
        return ProcessResult(f"{major}.{minor}.{build}", 0)
    except Exception as e:
        logger.debug(f"Getting brew version failed: {e}", exc_info=True)
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
        process_results = proc.run(["docker", "-v"]).output.splitlines()[0].split(" ")[2].split(",")[0]
        major, minor, build = get_version_from_str(process_results)
        return ProcessResult(f"{major}.{minor}.{build}", 0)
    except Exception as e:
        logger.debug(f"Getting docker version failed: {e}", exc_info=True)
        return ProcessResult(
            (
                "None found.\nDocker required to `run algokit sandbox` command;"
                " install via https://docs.docker.com/get-docker/"
            ),
            1,
        )


def get_docker_compose_info() -> ProcessResult:
    try:
        process_results = proc.run(["docker-compose", "-v"])
        docker_compose_version = process_results.output.splitlines()[0].split(" v")[2]
        minimum_version_met = is_minimum_version(docker_compose_version, DOCKER_COMPOSE_MINIMUM_VERSION)
        return ProcessResult(
            (
                docker_compose_version
                if minimum_version_met
                else f"{docker_compose_version}{DOCKER_COMPOSE_MINIMUM_VERSION_MESSAGE}"
            ),
            process_results.exit_code if minimum_version_met else 1,
        )
    except Exception as e:
        logger.debug(f"Getting docker compose version failed: {e}", exc_info=True)
        return ProcessResult(f"None found. {DOCKER_COMPOSE_MINIMUM_VERSION_MESSAGE}", 1)


def get_git_info(system: str) -> ProcessResult:
    try:
        process_results = proc.run(["git", "--version"]).output.splitlines()[0].split(" ")[2]
        major, minor, build = get_version_from_str(process_results)
        return ProcessResult(f"{major}.{minor}.{build}", 0)
    except Exception as e:
        logger.debug(f"Getting git version failed: {e}", exc_info=True)
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
        return ProcessResult(
            f"{sys_version_info.major}.{sys_version_info.minor}.{sys_version_info.micro} (location: {sys_executable})",
            0,
        )
    except Exception as e:
        logger.debug(f"Getting AlgoKit python version failed: {e}", exc_info=True)
        return ProcessResult("None found.", 1)


def get_global_python_info(python_command_name: str) -> ProcessResult:
    try:
        major, minor, build = get_version_from_str(
            proc.run([python_command_name, "--version"]).output.splitlines()[0].split(" ")[1]
        )
        global_python3_location = shutil.which(python_command_name)
        return ProcessResult(f"{major}.{minor}.{build} (location: {global_python3_location})", 0)
    except Exception as e:
        logger.debug(f"Getting python version failed: {e}", exc_info=True)
        return ProcessResult("None found.", 1)


def get_pipx_info() -> ProcessResult:
    try:
        major, minor, build = get_version_from_str(proc.run(["pipx", "--version"]).output.splitlines()[0])
        return ProcessResult(f"{major}.{minor}.{build}", 0)
    except Exception as e:
        logger.debug(f"Getting pipx version failed: {e}", exc_info=True)
        return ProcessResult(
            "None found.\nPipx is required to install Poetry; install via https://pypa.github.io/pipx/", 1
        )


def get_poetry_info() -> ProcessResult:
    try:
        process_results = proc.run(["poetry", "--version"]).output.splitlines()[-1].split("version ")[1].split(")")[0]
        major, minor, build = get_version_from_str(process_results)
        return ProcessResult(f"{major}.{minor}.{build}", 0)
    except Exception as e:
        logger.debug(f"Getting poetry version failed: {e}", exc_info=True)
        return ProcessResult(
            (
                "None found.\nPoetry is required for some Python-based templates; install via `algokit bootstrap` "
                "within project directory, or via https://python-poetry.org/docs/#installation"
            ),
            1,
        )


def get_node_info() -> ProcessResult:
    try:
        process_results = proc.run(["node", "-v"]).output.splitlines()[0].split("v")[1]
        major, minor, build = get_version_from_str(process_results)
        return ProcessResult(f"{major}.{minor}.{build}", 0)
    except Exception as e:
        logger.debug(f"Getting node version failed: {e}", exc_info=True)
        return ProcessResult(
            (
                "None found.\nNode.js is required for some Node.js-based templates; install via `algokit bootstrap` "
                "within project directory, or via https://nodejs.dev/en/learn/how-to-install-nodejs/"
            ),
            1,
        )


def get_npm_info(system: str) -> ProcessResult:
    try:
        process_results = proc.run(["npm" if system != "windows" else "npm.cmd", "-v"]).output.splitlines()[0]
        major, minor, build = get_version_from_str(process_results)
        return ProcessResult(f"{major}.{minor}.{build}", 0)
    except Exception as e:
        logger.debug(f"Getting npm version failed: {e}", exc_info=True)
        return ProcessResult("None found.", 1)


def is_minimum_version(system_version: str, minimum_version: str) -> bool:
    system_version_as_tuple = tuple(map(int, (system_version.split("."))))
    minimum_version_as_tuple = tuple(map(int, (minimum_version.split("."))))
    return system_version_as_tuple >= minimum_version_as_tuple


def get_version_from_str(version: str) -> tuple[int, int, int]:
    # take only the first three parts x.y.z of the version to ignore weird version
    major, minor, build = map(int, version.split(".")[:3])
    return major, minor, build
