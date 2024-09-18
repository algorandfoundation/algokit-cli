from __future__ import annotations

import enum
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, cast

import httpx

from algokit.core.conf import get_app_config_dir
from algokit.core.config_commands.container_engine import get_container_engine
from algokit.core.proc import RunResult, run, run_interactive

logger = logging.getLogger(__name__)

DOCKER_COMPOSE_MINIMUM_VERSION = "2.5.0"
PODMAN_COMPOSE_MINIMUM_VERSION = "1.0.6"


SANDBOX_BASE_NAME = "sandbox"
CONTAINER_ENGINE_CONFIG_FILE = get_app_config_dir() / "active-container-engine"


class ContainerEngine(str, enum.Enum):
    DOCKER = "docker"
    PODMAN = "podman"

    def __str__(self) -> str:
        return self.value


class ComposeFileStatus(enum.Enum):
    MISSING = enum.auto()
    UP_TO_DATE = enum.auto()
    OUT_OF_DATE = enum.auto()


def get_min_compose_version() -> str:
    container_engine = get_container_engine()
    return (
        DOCKER_COMPOSE_MINIMUM_VERSION if container_engine == ContainerEngine.DOCKER else PODMAN_COMPOSE_MINIMUM_VERSION
    )


class ComposeSandbox:
    def __init__(self, name: str = SANDBOX_BASE_NAME, config_path: Path | None = None) -> None:
        self.name = SANDBOX_BASE_NAME if name == SANDBOX_BASE_NAME else f"{SANDBOX_BASE_NAME}_{name}"
        self.directory = (config_path or get_app_config_dir()) / self.name
        if not self.directory.exists():
            logger.debug(f"The {self.name} directory does not exist yet; creating it")
            self.directory.mkdir()
        self._conduit_yaml = get_conduit_yaml()
        self._latest_yaml = get_docker_compose_yml(name=f"algokit_{self.name}")
        self._latest_config_json = get_config_json()
        self._latest_algod_network_template = get_algod_network_template()
        self._latest_proxy_config = get_proxy_config()

    @property
    def compose_file_path(self) -> Path:
        return self.directory / "docker-compose.yml"

    @property
    def conduit_file_path(self) -> Path:
        return self.directory / "conduit.yml"

    @property
    def algod_config_file_path(self) -> Path:
        return self.directory / "algod_config.json"

    @property
    def algod_network_template_file_path(self) -> Path:
        return self.directory / "algod_network_template.json"

    @property
    def proxy_config_file_path(self) -> Path:
        return self.directory / "nginx.conf"

    @classmethod
    def from_environment(cls) -> ComposeSandbox | None:
        try:
            run_results = run(
                [get_container_engine(), "compose", "ls", "--format", "json", "--filter", "name=algokit_sandbox*"],
                bad_return_code_error_message="Failed to list running LocalNet",
            )
            if run_results.exit_code != 0:
                return None
        except Exception as err:
            logger.debug(f"Error checking for existing sandbox: {err}", exc_info=True)
            return None

        try:
            json_lines = cls._extract_json_lines(run_results.output)
            if not json_lines:
                return None

            data = json.loads(json_lines[0])
            return cls._create_instance_from_data(data)
        except (json.JSONDecodeError, KeyError, IndexError) as err:
            logger.info(f"Error checking config file: {err}", exc_info=True)
            return None

    @staticmethod
    def _extract_json_lines(output: str) -> list[str]:
        valid_json_lines = []
        for line in output.splitlines():
            # strip ANSI color codes
            parsed_line = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", line)
            try:
                json.loads(parsed_line)
                valid_json_lines.append(parsed_line)
            except json.JSONDecodeError:
                continue
        return valid_json_lines

    @classmethod
    def _create_instance_from_data(cls, data: list[dict[str, Any]]) -> ComposeSandbox | None:
        for item in data:
            config_file = item.get("ConfigFiles", "").split(",")[0]
            full_name = Path(config_file).parent.name
            name = (
                full_name.replace(f"{SANDBOX_BASE_NAME}_", "")
                if full_name.startswith(f"{SANDBOX_BASE_NAME}_")
                else full_name
            )
            return cls(name)
        return None

    def set_algod_dev_mode(self, *, dev_mode: bool) -> None:
        content = self.algod_network_template_file_path.read_text()
        new_value = "true" if dev_mode else "false"
        new_content = re.sub(r'"DevMode":\s*(true|false)', f'"DevMode": {new_value}', content)
        self.algod_network_template_file_path.write_text(new_content)

    def is_algod_dev_mode(self) -> bool:
        content = self.algod_network_template_file_path.read_text()
        search = re.search(r'"DevMode":\s*(true|false)', content)
        return search is not None and search.group(1) == "true"

    def compose_file_status(self) -> ComposeFileStatus:
        try:
            compose_content = self.compose_file_path.read_text()
            config_content = self.algod_config_file_path.read_text()
            algod_network_template_content = self.algod_network_template_file_path.read_text()
            proxy_config_content = self.proxy_config_file_path.read_text()

        except FileNotFoundError:
            # treat as out of date if compose file exists but algod config doesn't
            # so that existing setups aren't suddenly reset
            if self.compose_file_path.exists():
                return ComposeFileStatus.OUT_OF_DATE
            return ComposeFileStatus.MISSING
        else:
            algod_network_json_content = json.loads(
                algod_network_template_content.replace("NUM_ROUNDS", '"NUM_ROUNDS"')
            )
            latest_algod_network_json_content = json.loads(
                self._latest_algod_network_template.replace("NUM_ROUNDS", '"NUM_ROUNDS"')
            )

            del algod_network_json_content["Genesis"]["DevMode"]
            del latest_algod_network_json_content["Genesis"]["DevMode"]

            if (
                compose_content == self._latest_yaml
                and config_content == self._latest_config_json
                and algod_network_json_content == latest_algod_network_json_content
                and proxy_config_content == self._latest_proxy_config
            ):
                return ComposeFileStatus.UP_TO_DATE
            else:
                return ComposeFileStatus.OUT_OF_DATE

    def write_compose_file(self) -> None:
        self.conduit_file_path.write_text(self._conduit_yaml)
        self.compose_file_path.write_text(self._latest_yaml)
        self.algod_config_file_path.write_text(self._latest_config_json)
        self.algod_network_template_file_path.write_text(self._latest_algod_network_template)
        self.proxy_config_file_path.write_text(self._latest_proxy_config)

    def _run_compose_command(
        self,
        compose_args: str,
        stdout_log_level: int = logging.INFO,
        bad_return_code_error_message: str | None = None,
    ) -> RunResult:
        return run(
            [get_container_engine(), "compose", *compose_args.split()],
            cwd=self.directory,
            stdout_log_level=stdout_log_level,
            bad_return_code_error_message=bad_return_code_error_message,
        )

    def up(self) -> None:
        logger.info("Starting AlgoKit LocalNet now...")
        self._run_compose_command(
            f"up --detach --quiet-pull{' --wait' if get_container_engine() == ContainerEngine.DOCKER else ''}",
            bad_return_code_error_message="Failed to start LocalNet",
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
        logger.info("Cleaning up the running AlgoKit LocalNet...")
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
            [get_container_engine(), "compose", *compose_args],
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
            json_lines = self._extract_json_lines(run_results.output)
            data = [json.loads(line) for line in json_lines]

        assert isinstance(data, list)
        return cast(list[dict[str, Any]], data)

    def _get_local_image_versions(self, image_name: str) -> list[str]:
        """
        Get the local versions of a Docker image. Note that a single image may be pulled from multiple repo digests.
        """
        try:
            arg = "{{range .RepoDigests}}{{println .}}{{end}}"
            local_versions_output = run([get_container_engine(), "image", "inspect", image_name, "--format", arg])
            return [line.split("@")[1] if "@" in line else line for line in local_versions_output.output.splitlines()]
        except Exception as e:
            logger.debug(f"Failed to get local image versions: {e}", exc_info=True)
            return []

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
            logger.debug(f"Error checking image status: {err}", exc_info=True)
            return None

    def is_image_up_to_date(self, image_name: str) -> bool:
        local_versions = self._get_local_image_versions(image_name)
        latest_version = self._get_latest_image_version(image_name)
        return latest_version is None or latest_version in local_versions

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
DEFAULT_INDEXER_SERVER = "http://localhost"
DEFAULT_ALGOD_TOKEN = "a" * 64
DEFAULT_INDEXER_TOKEN = "a" * 64
DEFAULT_ALGOD_PORT = 4001
DEFAULT_INDEXER_PORT = 8980
DEFAULT_WAIT_FOR_ALGOD = 60
DEFAULT_HEALTH_TIMEOUT = 1
ALGOD_HEALTH_URL = f"{DEFAULT_ALGOD_SERVER}:{DEFAULT_ALGOD_PORT}/v2/status"
INDEXER_IMAGE = "algorand/indexer:latest"
ALGORAND_IMAGE = "algorand/algod:latest"
CONDUIT_IMAGE = "algorand/conduit:latest"


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
        ' "IncomingConnectionsLimit": 0, "Archival":true, "isIndexerActive":false, "EnableDeveloperAPI":true}'
    )


def get_algod_network_template() -> str:
    return """{
    "Genesis": {
      "NetworkName": "followermodenet",
      "RewardsPoolBalance": 0,
      "FirstPartKeyRound": 0,
      "LastPartKeyRound": NUM_ROUNDS,
      "Wallets": [
        {
          "Name": "Wallet1",
          "Stake": 40,
          "Online": true
        },
        {
          "Name": "Wallet2",
          "Stake": 40,
          "Online": true
        },
        {
          "Name": "Wallet3",
          "Stake": 20,
          "Online": true
        }
      ],
      "DevMode": true
    },
    "Nodes": [
      {
        "Name": "data",
        "IsRelay": true,
        "Wallets": [
          {
            "Name": "Wallet1",
            "ParticipationOnly": false
          },
          {
            "Name": "Wallet2",
            "ParticipationOnly": false
          },
          {
            "Name": "Wallet3",
            "ParticipationOnly": false
          }
        ]
      },
      {
        "Name": "follower",
        "IsRelay": false,
        "ConfigJSONOverride":
        "{\\"EnableFollowMode\\":true,\\"EndpointAddress\\":\\"0.0.0.0:8081\\",\\"MaxAcctLookback\\":64,\\"CatchupParallelBlocks\\":64,\\"CatchupBlockValidateMode\\":3}"
      }
    ]
  }
"""


def get_conduit_yaml() -> str:
    return """# Log verbosity: PANIC, FATAL, ERROR, WARN, INFO, DEBUG, TRACE
log-level: INFO

# If no log file is provided logs are written to stdout.
#log-file:

# Number of retries to perform after a pipeline plugin error.
retry-count: 10

# Time duration to wait between retry attempts.
retry-delay: "1s"

# Optional filepath to use for pidfile.
#pid-filepath: /path/to/pidfile

# Whether or not to print the conduit banner on startup.
hide-banner: false

# When enabled prometheus metrics are available on '/metrics'
metrics:
  mode: OFF
  addr: ":9999"
  prefix: "conduit"

# The importer is typically an algod follower node.
importer:
  name: algod
  config:
    # The mode of operation, either "archival" or "follower".
    # * archival mode allows you to start processing on any round but does not
    # contain the ledger state delta objects required for the postgres writer.
    # * follower mode allows you to use a lightweight non-archival node as the
    # data source. In addition, it will provide ledger state delta objects to
    # the processors and exporter.
    mode: "follower"

    # Algod API address.
    netaddr: "http://algod:8081"

    # Algod API token.
    token: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

# Zero or more processors may be defined to manipulate what data
# reaches the exporter.
processors:

# An exporter is defined to do something with the data.
exporter:
  name: postgresql
  config:
    # Pgsql connection string
    # See https://github.com/jackc/pgconn for more details
    connection-string: "host=indexer-db port=5432 user=algorand password=algorand dbname=indexerdb"

    # Maximum connection number for connection pool
    # This means the total number of active queries that can be running
    # concurrently can never be more than this
    max-conn: 20
"""


def get_proxy_config(algod_port: int = DEFAULT_ALGOD_PORT, kmd_port: int = 4002) -> str:
    return f"""worker_processes 1;

events {{
  worker_connections 1024;
}}

http {{
  access_log off;

  resolver 127.0.0.11 ipv6=off valid=10s;
  resolver_timeout 5s;
  client_max_body_size 0;

  map $request_method$http_access_control_request_private_network $cors_allow_private_network {{
    "OPTIONStrue" "true";
    default "";
  }}

  add_header Access-Control-Allow-Private-Network $cors_allow_private_network;

  server {{
    listen {algod_port};

    location / {{
      proxy_http_version 1.1;
      proxy_read_timeout 120s;
      proxy_set_header Host $host;
      proxy_set_header Connection "";
      proxy_pass_header Server;
      set $target http://algod:8080;
      proxy_pass $target;
    }}
  }}

  server {{
    listen {kmd_port};

    location / {{
      proxy_http_version 1.1;
      proxy_set_header Host $host;
      proxy_set_header Connection "";
      proxy_pass_header Server;
      set $target http://algod:7833;
      proxy_pass $target;
    }}
  }}

  server {{
    listen 8980;

    location / {{
      proxy_http_version 1.1;
      proxy_set_header Host $host;
      proxy_set_header Connection "";
      proxy_pass_header Server;
      set $target http://indexer:8980;
      proxy_pass $target;
    }}
  }}
}}
    """


def get_docker_compose_yml(
    name: str = "algokit_sandbox",
    algod_port: int = DEFAULT_ALGOD_PORT,
    kmd_port: int = 4002,
    tealdbg_port: int = 9392,
) -> str:
    return f"""name: "{name}"

services:
  algod:
    container_name: "{name}_algod"
    image: {ALGORAND_IMAGE}
    ports:
      - 7833
      - {tealdbg_port}:9392
    environment:
      START_KMD: 1
      KMD_TOKEN: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      TOKEN: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      ADMIN_TOKEN: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      GOSSIP_PORT: 10000
    init: true
    volumes:
      - type: bind
        source: ./algod_config.json
        target: /etc/algorand/config.json
      - type: bind
        source: ./algod_network_template.json
        target: /etc/algorand/template.json
      - ./goal_mount:/root/goal_mount

  conduit:
    container_name: "{name}_conduit"
    image: {CONDUIT_IMAGE}
    restart: unless-stopped
    volumes:
      - type: bind
        source: ./conduit.yml
        target: /etc/algorand/conduit.yml
    depends_on:
      - indexer-db
      - algod

  indexer-db:
    container_name: "{name}_postgres"
    image: postgres:16-alpine
    ports:
      - 5443:5432
    user: postgres
    environment:
      POSTGRES_USER: algorand
      POSTGRES_PASSWORD: algorand
      POSTGRES_DB: indexerdb

  indexer:
    container_name: "{name}_indexer"
    image: {INDEXER_IMAGE}
    restart: unless-stopped
    command: daemon --enable-all-parameters
    environment:
      INDEXER_POSTGRES_CONNECTION_STRING: "host=indexer-db port=5432 user=algorand password=algorand dbname=indexerdb sslmode=disable"
    depends_on:
      - conduit

  proxy:
    container_name: "{name}_proxy"
    image: nginx:1.27.0-alpine
    restart: unless-stopped
    ports:
      - {algod_port}:{algod_port}
      - {kmd_port}:{kmd_port}
      - 8980:8980
    volumes:
      - type: bind
        source: ./nginx.conf
        target: /etc/nginx/nginx.conf
    depends_on:
      - algod
      - indexer
"""  # noqa: E501


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

        results["Port"] = DEFAULT_INDEXER_PORT
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


COMPOSE_VERSION_COMMAND = [get_container_engine(), "compose", "version", "--format", "json"]
