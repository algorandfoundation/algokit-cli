import dataclasses
import logging
import platform
from datetime import datetime, timezone

from algokit.core import proc

logger = logging.getLogger(__name__)

DOCKER_COMPOSE_MINIMUM_VERSION = "2.5"

docker_compose_minimum_version_message = (
    f"\nDocker Compose {DOCKER_COMPOSE_MINIMUM_VERSION} required to `run algokit sandbox command`; "
    "install via https://docs.docker.com/compose/install/"
)


@dataclasses.dataclass
class ProcessResult:
    info: str
    exit_code: int


class DoctorFunctions:
    def get_date(self) -> ProcessResult:
        return ProcessResult(format(datetime.now(timezone.utc).astimezone().isoformat()), 0)

    def get_algokit_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["pip", "show", "AlgoKit"])
            algokit_info: dict[str, str] = {}
            for line in process_results.output.splitlines():
                line_parts = line.split(":")
                algokit_info[line_parts[0].lower().strip()] = line_parts[1].strip()
            return ProcessResult(f"{algokit_info['version']} {algokit_info['location']}", process_results.exit_code)
        except Exception:
            return ProcessResult("Not found", 1)

    def get_choco_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["choco"])
            return ProcessResult(process_results.output.splitlines()[0].split(" v")[1], process_results.exit_code)
        except Exception:
            return ProcessResult("None found", 1)

    def get_brew_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["brew", "-v"])
            return ProcessResult(process_results.output.splitlines()[0].split(" ")[1], process_results.exit_code)
        except Exception:
            return ProcessResult("None found", 1)

    def get_os(self, os_type: str) -> ProcessResult:
        os_version = ""
        if os_type == "windows":
            os_version = platform.win32_ver()[0]
        elif os_type == "darwin":
            os_version = platform.mac_ver()[0]
        else:
            os_version = platform.version()
        return ProcessResult(f"{os_type} {os_version}", 0)

    def get_docker_info(self) -> ProcessResult:
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

    def get_docker_compose_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["docker-compose", "-v"])
            docker_compose_version = process_results.output.splitlines()[0].split(" v")[2]
            minimum_version_met = self.is_minimum_version(docker_compose_version, DOCKER_COMPOSE_MINIMUM_VERSION)
            return ProcessResult(
                (
                    docker_compose_version
                    if minimum_version_met
                    else f"{docker_compose_version}.\n{docker_compose_minimum_version_message}"
                ),
                process_results.exit_code if minimum_version_met else 1,
            )
        except Exception:
            return ProcessResult(f"None found. {docker_compose_minimum_version_message}", 1)

    def get_git_info(self, system: str) -> ProcessResult:
        try:
            process_results = proc.run(["git", "-v"])
            return ProcessResult(process_results.output.splitlines()[0].split(" ")[2], process_results.exit_code)
        except Exception:
            if system == "windows":
                return ProcessResult(
                    (
                        "Git required to `run algokit init`; install via `choco install git` if using Chocolatey or "
                        "via https://github.com/git-guides/install-git#install-git-on-windows"
                    ),
                    1,
                )
            else:
                return ProcessResult(
                    "Git required to run algokit init; " "install via https://github.com/git-guides/install-git", 1
                )

    def get_algokit_python_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["python", "--version"])
            return ProcessResult(process_results.output.splitlines()[0].split(" ")[1], process_results.exit_code)
        except Exception:
            return ProcessResult("None found.", 1)

    def get_global_python_info(self) -> ProcessResult:
        try:
            # [TODO] <version of first global path python3 version> <path> | None found
            process_results = proc.run(["python", "--version"])
            return ProcessResult(process_results.output.splitlines()[0].split(" ")[1], process_results.exit_code)
        except Exception:
            return ProcessResult("None found.", 1)

    def get_pipx_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["pipx", "--version"])
            return ProcessResult(process_results.output.splitlines()[0], process_results.exit_code)
        except Exception:
            return ProcessResult(
                "None found.\nPipx is required to install Poetry; install via https://pypa.github.io/pipx/", 1
            )

    def get_poetry_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["poetry", "--version"])
            poetry_version = process_results.output.splitlines()[-1].split("version ")[1].split(")")[0]
            return ProcessResult(poetry_version, process_results.exit_code)
        except Exception:
            return ProcessResult(
                (
                    "None found.\nPoetry is required for some Python-based templates; "
                    "install via algokit bootstrap within project directory, "
                    "or via https://python-poetry.org/docs/#installation"
                ),
                1,
            )

    def get_node_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["node", "-v"])
            return ProcessResult(process_results.output.splitlines()[0].split("v")[1], process_results.exit_code)
        except Exception:
            return ProcessResult(
                (
                    "None found.\nNode.js is required for some Node.js-based templates; "
                    "install via `algokit bootstrap` within project directory, "
                    "or via https://nodejs.dev/en/learn/how-to-install-nodejs/"
                ),
                1,
            )

    def get_npm_info(self) -> ProcessResult:
        try:
            process_results = proc.run(["npm", "-v"])
            return ProcessResult(process_results.output, process_results.exit_code)
        except Exception:
            return ProcessResult("None found", 1)

    def is_minimum_version(self, system_version: str, minimum_version: str) -> bool:
        system_version_as_tuple = tuple(map(int, (system_version.split("."))))
        minimum_version_as_tuple = tuple(map(int, (minimum_version.split("."))))
        return system_version_as_tuple >= minimum_version_as_tuple
