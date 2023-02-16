import enum
import json
import logging
from pathlib import Path
from typing import Any, cast

import httpx

from algokit.core.conf import get_app_config_dir
from algokit.core.proc import RunResult, run

logger = logging.getLogger(__name__)


DOCKER_COMPOSE_MINIMUM_VERSION = "2.5.0"


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
        logger.info("Starting AlgoKit LocalNet now...")
        self._run_compose_command(
            "up --detach --quiet-pull --wait", bad_return_code_error_message="Failed to start LocalNet"
        )
        logger.info("Started; execute `algokit localnet status` to check the status.")

    def stop(self) -> None:
        logger.info("Stopping AlgoKit LocalNet now...")
        self._run_compose_command("stop", bad_return_code_error_message="Failed to stop LocalNet")
        logger.info("Sandbox Stopped; execute `algokit localnet start` to start it again.")

    def down(self) -> None:
        logger.info("Deleting any existing LocalNet...")
        self._run_compose_command("down", stdout_log_level=logging.DEBUG)

    def pull(self) -> None:
        logger.info("Looking for latest Sandbox images from DockerHub...")
        self._run_compose_command("pull --ignore-pull-failures --quiet")

    def ps(self) -> list[dict[str, Any]]:
        run_results = self._run_compose_command("ps --format json", stdout_log_level=logging.DEBUG)
        if run_results.exit_code != 0:
            return []
        data = json.loads(run_results.output)
        assert isinstance(data, list)
        return cast(list[dict[str, Any]], data)


DEFAULT_ALGOD_SERVER = "http://localhost"
DEFAULT_ALGOD_TOKEN = "a" * 64
DEFAULT_ALGOD_PORT = 4001
DEFAULT_INDEXER_PORT = 8980


def get_docker_compose_yml(
    name: str = "algokit",
    algod_port: int = DEFAULT_ALGOD_PORT,
    kmd_port: int = 4002,
    tealdbg_port: int = 9392,
    indexer_port: int = DEFAULT_INDEXER_PORT,
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


def fetch_algod_status_data(service_info: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    try:
        # Docker image response
        # Search for DEFAULT_ALGOD_PORT in ports, if found use it, if not found this is an error
        if not any(item["PublishedPort"] == DEFAULT_ALGOD_PORT for item in service_info["Publishers"]):
            return {"Status": "Error"}

        results["Port"] = DEFAULT_ALGOD_PORT
        # container specific response
        with httpx.Client() as client:
            algod_headers = {"X-Algo-API-Token": DEFAULT_ALGOD_TOKEN}
            http_status_response = client.get(
                f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_ALGOD_PORT}/v1/status", headers=algod_headers, timeout=3
            )
            http_versions_response = client.get(
                f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_ALGOD_PORT}/versions", headers=algod_headers, timeout=3
            )
            if (
                http_status_response.status_code != httpx.codes.OK
                or http_versions_response.status_code != httpx.codes.OK
            ):
                return {"Status": "Error"}

            # status response
            status_response = http_status_response.json()
            results["Last round"] = status_response["lastRound"]
            results["Time since last round"] = "%.1fs" % status_response["timeSinceLastRound"]
            # genesis response
            genesis_response = http_versions_response.json()
            results["Genesis ID"] = genesis_response["genesis_id"]
            results["Genesis hash"] = genesis_response["genesis_hash_b64"]
            major_version = genesis_response["build"]["major"]
            minor_version = genesis_response["build"]["minor"]
            build_version = genesis_response["build"]["build_number"]
            results["Version"] = f"{major_version}.{minor_version}.{build_version}"
        return results
    except Exception as err:
        logger.debug(f"Error checking algod status: {err}", exc_info=True)
        return {"Status": "Error"}


def fetch_indexer_status_data(service_info: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    try:
        # Docker image response
        if not any(item["PublishedPort"] == DEFAULT_INDEXER_PORT for item in service_info["Publishers"]):
            return {"Status": "Error"}

        results["Port"] = service_info["Publishers"][0]["PublishedPort"]
        # container specific response
        http_response = httpx.get(f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_INDEXER_PORT}/health", timeout=5)

        if http_response.status_code != httpx.codes.OK:
            return {"Status": "Error"}

        response = http_response.json()
        results["Last round"] = response["round"]
        if "errors" in response:
            results["Error(s)"] = response["errors"]
        results["Version"] = response["version"]
        return results
    except Exception as err:
        logger.debug(f"Error checking indexer status: {err}", exc_info=True)
        return {"Status": "Error"}


DOCKER_COMPOSE_VERSION_COMMAND = ["docker", "compose", "version", "--format", "json"]


def parse_docker_compose_version_output(output: str) -> str:
    compose_version: dict[str, str] = json.loads(output)
    compose_version_str = compose_version.get("version", "")
    return compose_version_str.lstrip("v")
