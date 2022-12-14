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


class DoctorFunctions:
    def get_date(self) -> str:
        return format(datetime.now(timezone.utc).astimezone().isoformat())

    def get_algokit_info(self) -> str:
        algokit_info = self.get_installed_software_version(["pip", "show", "AlgoKit"])
        return f"{algokit_info['version']} {algokit_info['location']}"

    def get_choco_info(self) -> str:
        try:
            return proc.run(["choco"]).output.splitlines()[0].split(" v")[1]
        except Exception:
            return "None found"

    def get_brew_info(self) -> str:
        try:
            return proc.run(["brew", "-v"]).output.splitlines()[0].split(" ")[1]
        except Exception:
            return "None found"

    def get_os(self, os_type: str) -> str:
        os_version = ""
        if os_type == "windows":
            os_version = platform.win32_ver()[0]
        elif os_type == "darwin":
            os_version = platform.mac_ver()[0]
        else:
            os_version = platform.version()
        return f"{os_type} {os_version}"

    def get_docker_info(self) -> str:
        try:
            docker_version = proc.run(["docker", "-v"]).output.splitlines()[0].split(" ")[2].split(",")[0]
            return docker_version
        except Exception:
            return (
                "None found.\nDocker required to `run algokit sandbox` command;"
                " install via https://docs.docker.com/get-docker/"
            )

    def get_docker_compose_info(self) -> str:
        try:
            docker_compose_version = proc.run(["docker-compose", "-v"]).output.splitlines()[0].split(" v")[2]
            return (
                docker_compose_version
                if self.is_minimum_version(docker_compose_version, DOCKER_COMPOSE_MINIMUM_VERSION)
                else f"{docker_compose_version}.\n{docker_compose_minimum_version_message}"
            )
        except Exception:
            return f"None found. {docker_compose_minimum_version_message}"

    def get_git_info(self, system: str) -> str:
        try:
            git_version = proc.run(["git", "-v"]).output.splitlines()[0].split(" ")[2]
            return git_version
        except Exception:
            if system == "windows":
                return (
                    "Git required to `run algokit init`;"
                    "install via `choco install git` if using Chocolatey or "
                    "via https://github.com/git-guides/install-git#install-git-on-windows"
                )

            else:
                return "Git required to run algokit init; " "install via https://github.com/git-guides/install-git"

    def get_algokit_python_info(self) -> str:
        return proc.run(["python", "--version"]).output.splitlines()[0].split(" ")[1]

    def get_global_python_info(self) -> str:
        return "[TODO] <version of first global path python3 version> <path> | None found"

    def get_pipx_info(self) -> str:
        try:
            pipx_version = proc.run(["pipx", "--version"]).output.splitlines()[0]
            return pipx_version
        except Exception:
            return "None found.\nPipx is required to install Poetry; install via https://pypa.github.io/pipx/"

    def get_poetry_info(self) -> str:
        try:
            poetry_version = (
                proc.run(["poetry", "--version"]).output.splitlines()[-1].split("version ")[1].split(")")[0]
            )
            return poetry_version
        except Exception:
            return (
                "None found.\nPoetry is required for some Python-based templates; "
                "install via algokit bootstrap within project directory, "
                "or via https://python-poetry.org/docs/#installation"
            )

    def get_node_info(self) -> str:
        try:
            node_version = proc.run(["node", "-v"]).output.splitlines()[0].split("v")[1]
            return node_version
        except Exception:
            return (
                "None found.\nNode.js is required for some Node.js-based templates; "
                "install via `algokit bootstrap` within project directory, "
                "or via https://nodejs.dev/en/learn/how-to-install-nodejs/"
            )

    def get_npm_info(self) -> str:
        try:
            npm_version = proc.run(["npm", "-v"]).output
            return npm_version
        except Exception:
            return "None found"

    def get_installed_software_version(self, command: list[str]) -> dict[str, str]:
        package_info_lines = proc.run(command).output.splitlines()
        results: dict[str, str] = {}
        for line in package_info_lines:
            line_parts = line.split(":")
            results[line_parts[0].lower().strip()] = line_parts[1].strip()
        return results

    def is_minimum_version(self, system_version: str, minimum_version: str) -> bool:
        system_version_as_tuple = tuple(map(int, (system_version.split("."))))
        minimum_version_as_tuple = tuple(map(int, (minimum_version.split("."))))
        return system_version_as_tuple >= minimum_version_as_tuple
