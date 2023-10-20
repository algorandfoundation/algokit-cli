import enum
import json
import logging
import time
from pathlib import Path
from typing import Any, cast

import httpx

from algokit.core.conf import get_app_config_dir
from algokit.core.proc import RunResult, run, run_interactive

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
        self._latest_config_json = get_config_json()

    @property
    def compose_file_path(self) -> Path:
        return self.directory / "docker-compose.yml"

    @property
    def algod_config_file_path(self) -> Path:
        return self.directory / "algod_config.json"

    def compose_file_status(self) -> ComposeFileStatus:
        try:
            compose_content = self.compose_file_path.read_text()
            config_content = self.algod_config_file_path.read_text()
        except FileNotFoundError:
            # treat as out of date if compose file exists but algod config doesn't
            # so that existing setups aren't suddenly reset
            if self.compose_file_path.exists():
                return ComposeFileStatus.OUT_OF_DATE
            return ComposeFileStatus.MISSING
        else:
            if compose_content == self._latest_yaml and config_content == self._latest_config_json:
                return ComposeFileStatus.UP_TO_DATE
            else:
                return ComposeFileStatus.OUT_OF_DATE

    def write_compose_file(self) -> None:
        self.compose_file_path.write_text(self._latest_yaml)
        self.algod_config_file_path.write_text(self._latest_config_json)

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
        logger.debug("AlgoKit LocalNet started, waiting for health check")
        if _wait_for_algod():
            logger.info("Started; execute `algokit explore` to explore LocalNet in a web user interface.")
        else:
            logger.warning("AlgoKit LocalNet failed to return a successful health check")

    def stop(self) -> None:
        logger.info("Stopping AlgoKit LocalNet now...")
        self._run_compose_command("stop", bad_return_code_error_message="Failed to stop LocalNet")
        logger.info("LocalNet Stopped; execute `algokit localnet start` to start it again.")

    def down(self) -> None:
        logger.info("Deleting any existing LocalNet...")
        self._run_compose_command("down", stdout_log_level=logging.DEBUG)

    def pull(self) -> None:
        logger.info("Fetching any container updates from DockerHub...")
        self._run_compose_command("pull --ignore-pull-failures --quiet")

    def logs(self, *, follow: bool = False, no_color: bool = False, tail: str | None = None) -> None:
        compose_args = ["logs"]
        if follow:
            compose_args += ["--follow"]
        if no_color:
            compose_args += ["--no-color"]
        if tail is not None:
            compose_args += ["--tail", tail]
        run_interactive(
            ["docker", "compose", *compose_args],
            cwd=self.directory,
            bad_return_code_error_message="Failed to get logs, are the containers running?",
        )

    def ps(self, service_name: str | None = None) -> list[dict[str, Any]]:
        run_results = self._run_compose_command(
            f"ps {service_name or ''} --format json", stdout_log_level=logging.DEBUG
        )
        if run_results.exit_code != 0:
            return []

        # `docker compose ps --format json` on version < 2.21.0 outputs a JSON arary
        if run_results.output.startswith("["):
            data = json.loads(run_results.output)
        # `docker compose ps --format json` on version >= 2.21.0 outputs seperate JSON objects, each on a new line
        else:
            data = [json.loads(line) for line in run_results.output.splitlines() if line]

        assert isinstance(data, list)
        return cast(list[dict[str, Any]], data)

    def _get_local_image_version(self, image_name: str) -> str | None:
        """
        Get the local version of a Docker image
        """
        try:
            arg = '{{index (split (index .RepoDigests 0) "@") 1}}'
            local_version = run(
                ["docker", "image", "inspect", image_name, "--format", arg],
                cwd=self.directory,
                bad_return_code_error_message="Failed to get image inspect",
            )

            return local_version.output.strip()
        except Exception:
            return None

    def _get_latest_image_version(self, image_name: str) -> str | None:
        """
        Get the latest version of a Docker image from Docker Hub
        """
        args = image_name.split(":")
        name = args[0]
        tag = args[1] if len(args) > 1 else "latest"
        url = f"https://registry.hub.docker.com/v2/repositories/{name}/tags/{tag}"
        try:
            data = httpx.get(url=url)
            return str(data.json()["digest"])
        except Exception as err:
            logger.debug(f"Error checking indexer status: {err}", exc_info=True)
            return None

    def is_image_up_to_date(self, image_name: str) -> bool:
        local_version = self._get_local_image_version(image_name)
        latest_version = self._get_latest_image_version(image_name)
        return local_version is None or latest_version is None or local_version == latest_version

    def check_docker_compose_for_new_image_versions(self) -> None:
        is_indexer_up_to_date = self.is_image_up_to_date(INDEXER_IMAGE)
        if is_indexer_up_to_date is False:
            logger.warning(
                "indexer has a new version available, run `algokit localnet reset --update` to get the latest version"
            )

        is_algorand_up_to_date = self.is_image_up_to_date(ALGORAND_IMAGE)
        if is_algorand_up_to_date is False:
            logger.warning(
                "algod has a new version available, run `algokit localnet reset --update` to get the latest version"
            )


DEFAULT_ALGOD_SERVER = "http://localhost"
DEFAULT_ALGOD_TOKEN = "a" * 64
DEFAULT_ALGOD_PORT = 4001
DEFAULT_INDEXER_PORT = 8980
DEFAULT_WAIT_FOR_ALGOD = 60
DEFAULT_HEALTH_TIMEOUT = 1
ALGOD_HEALTH_URL = f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_ALGOD_PORT}/v2/status"
INDEXER_IMAGE = "makerxau/algorand-indexer-dev:latest"
ALGORAND_IMAGE = "algorand/algod:latest"


def _wait_for_algod() -> bool:
    end_time = time.time() + DEFAULT_WAIT_FOR_ALGOD
    last_exception: httpx.RequestError | None = None
    while time.time() < end_time:
        try:
            health = httpx.get(
                ALGOD_HEALTH_URL, timeout=DEFAULT_HEALTH_TIMEOUT, headers={"X-Algo-API-Token": DEFAULT_ALGOD_TOKEN}
            )
        except httpx.RequestError as ex:
            last_exception = ex
        else:
            if health.is_success:
                logger.debug("AlgoKit LocalNet health check successful, algod is ready")
                return True
            logger.debug(f"AlgoKit LocalNet health check returned {health.status_code}, waiting")
        time.sleep(DEFAULT_HEALTH_TIMEOUT)
    if last_exception:
        logger.debug("AlgoKit LocalNet health request failed", exc_info=last_exception)
    return False


def get_config_json() -> str:
    return (
        '{ "Version": 12, "GossipFanout": 1, "EndpointAddress": "0.0.0.0:8080", "DNSBootstrapID": "",'
        ' "IncomingConnectionsLimit": 0, "Archival":false, "isIndexerActive":false, "EnableDeveloperAPI":true}"'
    )


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
    image: {ALGORAND_IMAGE}
    ports:
      - {algod_port}:8080
      - {kmd_port}:7833
      - {tealdbg_port}:9392
    environment:
      DEV_MODE: 1
      START_KMD: 1
      TOKEN: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      KMD_TOKEN: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    volumes:
      - type: bind
        source: ./algod_config.json
        target: /etc/algorand/config.json
      - ./goal_mount:/root/goal_mount

  indexer:
    container_name: {name}_indexer
    image: {INDEXER_IMAGE}
    ports:
      - {indexer_port}:8980
    restart: unless-stopped
    environment:
      ALGOD_HOST: algod
      ALGOD_PORT: 8080
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
    ports:
      - 5443:5432
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
                f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_ALGOD_PORT}/v2/status", headers=algod_headers, timeout=3
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
            results["Last round"] = status_response["last-round"]
            results["Time since last round"] = "%.1fs" % (status_response["time-since-last-round"] / 1e9)
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
        health_url = f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_INDEXER_PORT}/health"
        http_response = httpx.get(health_url, timeout=5)

        if http_response.status_code != httpx.codes.OK:
            return {"Status": "Error"}

        response = http_response.json()
        logger.debug(f"{health_url} response: {response}")
        results["Last round"] = response["round"]
        results["Version"] = response["version"]
        return results
    except Exception as err:
        logger.debug(f"Error checking indexer status: {err}", exc_info=True)
        return {"Status": "Error"}


DOCKER_COMPOSE_VERSION_COMMAND = ["docker", "compose", "version", "--format", "json"]
