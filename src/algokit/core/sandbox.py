import enum
import logging
from pathlib import Path

from algokit.core.conf import get_app_config_dir
from algokit.core.exec import RunResult, run

logger = logging.getLogger(__name__)


class ComposeFileStatus(enum.Enum):
    MISSING = enum.auto()
    UP_TO_DATE = enum.auto()
    OUT_OF_DATE = enum.auto()


class ComposeSandbox:
    def __init__(self) -> None:
        self.directory = get_app_config_dir() / "sandbox"
        if not self.directory.exists():
            logger.debug("Sandbox directory does not exist yet; creating it")
            self.directory.mkdir()
        self._latest_yaml = get_docker_compose_yml()

    @property
    def compose_file_path(self) -> Path:
        return self.directory / "docker-compose.yml"

    def compose_file_status(self) -> ComposeFileStatus:
        try:
            content = self.compose_file_path.read_text()
        except FileNotFoundError:
            return ComposeFileStatus.MISSING
        else:
            if content == self._latest_yaml:
                return ComposeFileStatus.UP_TO_DATE
            else:
                return ComposeFileStatus.OUT_OF_DATE

    def write_compose_file(self) -> None:
        self.compose_file_path.write_text(self._latest_yaml)

    def _run_compose_command(
        self,
        compose_args: str,
        stdout_log_level: int = logging.INFO,
        bad_return_code_error_message: str | None = None,
    ) -> RunResult:
        return run(
            ["docker", "compose", *compose_args.split()],
            cwd=self.directory,
            stdout_log_level=stdout_log_level,
            bad_return_code_error_message=bad_return_code_error_message,
        )

    def up(self) -> None:
        logger.info("Starting the AlgoKit sandbox now...")
        self._run_compose_command(
            "up --detach --quiet-pull --wait", bad_return_code_error_message="Failed to start Sandbox"
        )
        logger.info("Started; execute `algokit sandbox status` to check the status.")

    def down(self) -> None:
        logger.info("Deleting any existing Sandbox...")
        self._run_compose_command("down", stdout_log_level=logging.DEBUG)

    def pull(self) -> None:
        logger.info("Looking for latest Sandbox images from DockerHub...")
        self._run_compose_command("pull --ignore-pull-failures --quiet")


def get_docker_compose_yml(
    name: str = "algokit",
    algod_port: int = 4001,
    kmd_port: int = 4002,
    tealdbg_port: int = 9392,
    indexer_port: int = 8980,
) -> str:
    return f"""version: '3'
name: "{name}_sandbox"

services:
  algod:
    container_name: {name}_algod
    image: makerxau/algorand-sandbox-dev:latest
    ports:
      - {algod_port}:4001
      - {kmd_port}:4002
      - {tealdbg_port}:9392

  indexer:
    container_name: {name}_indexer
    image: makerxau/algorand-indexer-dev:latest
    ports:
      - {indexer_port}:8980
    restart: unless-stopped
    environment:
      ALGOD_HOST: algod
      POSTGRES_HOST: indexer-db
      POSTGRES_PORT: 5432
      POSTGRES_USER: algorand
      POSTGRES_PASSWORD: algorand
      POSTGRES_DB: indexer_db
    depends_on:
      - indexer-db
      - algod

  indexer-db:
    container_name: {name}_postgres
    image: postgres:13-alpine
    user: postgres
    environment:
      POSTGRES_USER: algorand
      POSTGRES_PASSWORD: algorand
      POSTGRES_DB: indexer_db
"""
