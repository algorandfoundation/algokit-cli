import logging
import platform
from datetime import datetime, timezone

from algokit.core import proc

logger = logging.getLogger(__name__)


class DoctorFunctions:
    def get_date(self) -> str:
        return f"Time: {format(datetime.now(timezone.utc).astimezone().isoformat())}\n"

    def get_algokit_version(self) -> str:
        algokit_info = self.get_installed_software_version(["pip", "show", "AlgoKit"])
        return f"AlgoKit: {algokit_info['version']} {algokit_info['location']}"

    def get_installed_software_version(self, command: list[str]) -> dict[str, str]:
        package_info_lines = proc.run(command).output.splitlines()
        results: dict[str, str] = {}
        for line in package_info_lines:
            line_parts = line.split(":")
            results[line_parts[0].lower().strip()] = line_parts[1].strip()
        return results

    def get_choco_info(self) -> str:
        choco_version = proc.run(["choco"]).output.splitlines()[0].split(" v")[1]
        return f"\nChocolatey installed version:{choco_version}"

    def get_brew_info(self) -> str:
        brew_version = proc.run(["brew", "-v"]).output.splitlines()[0].split(" ")[1]
        return f"\nBrew installed version: {brew_version}"

    def get_os(self, os_type: str) -> str:
        os_version = ""
        if os_type == "windows":
            os_version = platform.win32_ver()[0]
        elif os_type == "darwin":
            os_version = platform.mac_ver()[0]
        else:
            os_version = platform.version()
        return f"\nOS: {os_type} {os_version}"

    def get_docker_info(self) -> str:
        try:
            docker_version = proc.run(["docker", "-v"]).output.splitlines()[0].split(" ")[2].split(",")[0]
            return f"\nDocker: {docker_version}"
        except Exception:
            return (
                "\nDocker: None found"
                "\nDocker required to `run algokit sandbox` command; install via https://docs.docker.com/get-docker/"
            )

    def get_docker_compose_info(self) -> str:
        docker_compose_minimum_version_message = (
            "\nDocker Compose 2.5 required to `run algokit sandbox command`; "
            "install via https://docs.docker.com/compose/install/"
        )
        try:
            docker_version = proc.run(["docker-compose", "-v"]).output.splitlines()[0].split(" v")[2]
            message = f"\nDocker Compose: {docker_version}"
            if not docker_version.startswith("2.5"):
                message += f"{docker_compose_minimum_version_message}"
            return message
        except Exception:
            return f"\nDocker compose: None found{docker_compose_minimum_version_message}"

    def get_git_info(self, is_windows: bool) -> str:
        try:
            git_version = proc.run(["git", "-v"]).output.splitlines()[0].split(" ")[2]
            return f"Git: {git_version}"
        except Exception:
            if is_windows:
                return (
                    "\nGit required to `run algokit init`;"
                    "install via `choco install git` if using Chocolatey or "
                    "via https://github.com/git-guides/install-git#install-git-on-windows"
                )
            else:
                return (
                    "\nOtherwise: Git required to run algokit init; "
                    "install via https://github.com/git-guides/install-git"
                )

    def get_algokit_python_info(self) -> str:
        return "\n[TODO] AlgoKit Python: <version of algokit version> <path> (base path: <base path>)"

    def get_global_info(self) -> str:
        return "\n[TODO] Global Python: <version of first global path python3 version> <path> | None found"

    def get_pipx_info(self) -> str:
        try:
            pipx_version = proc.run(["pipx", "--version"]).output.splitlines()[0]
            return f"\nPipx: {pipx_version}"
        except Exception:
            return "\nPipx: None found\nPipx is required to install Poetry; install via https://pypa.github.io/pipx/"

    def get_poetry_info(self) -> str:
        try:
            poetry_version = (
                proc.run(["poetry", "--version"]).output.splitlines()[-1].split("version ")[1].split(")")[0]
            )
            return f"\nPoetry: {poetry_version}"
        except Exception:
            return (
                "\nPipx: None found\nPoetry is required for some Python-based templates; "
                "install via algokit bootstrap within project directory, "
                "or via https://python-poetry.org/docs/#installation"
            )

    def get_node_info(self) -> str:
        try:
            node_version = proc.run(["node", "-v"]).output.splitlines()[0].split("v")[1]
            return f"\nNode: {node_version}"
        except Exception:
            return (
                "\nNode: None found\nNode.js is required for some Node.js-based templates; "
                "install via algokit bootstrap within project directory, "
                "or via https://nodejs.dev/en/learn/how-to-install-nodejs/"
            )

    def get_npm_info(self) -> str:
        try:
            npm_version = proc.run(["npm", "-v"]).output
            return f"\nNpm: {npm_version}"
        except Exception:
            return "\nNpm: None found"
