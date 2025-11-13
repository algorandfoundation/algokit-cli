import copy
import json
from typing import TypedDict

import httpx
import pytest
from pytest_httpx import HTTPXMock

from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.mark.usefixtures("_mock_proc_with_running_localnet")
def test_localnet_status_successful(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    httpx_mock.add_response(
        url="http://localhost:4001/v2/status", json={"last-round": 1, "time-since-last-round": 15.3 * 1e9}
    )
    httpx_mock.add_response(
        url="http://localhost:4001/versions",
        json={
            "genesis_id": "{genesis_id}",
            "genesis_hash_b64": "{genesis_hash_b64}",
            "build": {"major": 1, "minor": 2, "build_number": 1},
        },
    )
    httpx_mock.add_response(
        url="http://localhost:8980/health", json={"round": 1, "errors": ["error"], "version": "v1.0"}
    )

    proc_mock.set_output(
        "docker compose ps --format json",
        [json.dumps(compose_ps_output)],
    )
    result = invoke("localnet status")

    assert result.exit_code == 0
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("_mock_proc_with_running_localnet")
def test_localnet_status_http_error(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    httpx_mock.add_response(
        url="http://localhost:4001/v2/status", json={"last-round": 1, "time-since-last-round": 15.3 * 1e9}
    )
    httpx_mock.add_response(
        url="http://localhost:4001/versions",
        json={
            "genesis_id": "{genesis_id}",
            "genesis_hash_b64": "{genesis_hash_b64}",
            "build": {"major": 1, "minor": 2, "build_number": 1},
        },
    )
    httpx_mock.add_exception(httpx.ReadTimeout("Unable to read within timeout"))

    proc_mock.set_output(
        "docker compose ps --format json",
        [json.dumps(compose_ps_output)],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("_mock_proc_with_running_localnet")
def test_localnet_status_unexpected_port(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    httpx_mock.add_response(
        url="http://localhost:4001/v2/status",
        json={"last-round": 1, "time-since-last-round": 15.3 * 1e9},
    )
    httpx_mock.add_response(
        url="http://localhost:4001/versions",
        json={
            "genesis_id": "{genesis_id}",
            "genesis_hash_b64": "{genesis_hash_b64}",
            "build": {"major": 1, "minor": 2, "build_number": 1},
        },
    )

    unexpected_port_compose_ps_output = copy.deepcopy(compose_ps_output)
    # Change the proxy indexer configuration to use a different port
    unexpected_port_compose_ps_output[4]["Publishers"][2]["TargetPort"] = 1234
    unexpected_port_compose_ps_output[4]["Publishers"][2]["PublishedPort"] = 1234

    proc_mock.set_output(
        "docker compose ps --format json",
        [json.dumps(unexpected_port_compose_ps_output)],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("_mock_proc_with_running_localnet")
def test_localnet_status_service_not_started(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    httpx_mock.add_response(
        url="http://localhost:8980/health", json={"round": 1, "errors": ["error"], "version": "v1.0"}
    )

    service_not_started_compose_ps_output = copy.deepcopy(compose_ps_output)
    # Change the algod state to stopped
    service_not_started_compose_ps_output[0]["State"] = "stopped"

    proc_mock.set_output(
        "docker compose ps --format json",
        [json.dumps(service_not_started_compose_ps_output)],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("_mock_proc_with_running_localnet")
def test_localnet_status_docker_error(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    httpx_mock.add_response(
        url="http://localhost:4001/v2/status", json={"last-round": 1, "time-since-last-round": 15.3 * 1e9}
    )
    httpx_mock.add_response(
        url="http://localhost:4001/versions",
        json={
            "genesis_id": "{genesis_id}",
            "genesis_hash_b64": "{genesis_hash_b64}",
            "build": {"major": 1, "minor": 2, "build_number": 1},
        },
    )

    docker_error_compose_ps_output = copy.deepcopy(compose_ps_output)
    # Remove proxy indexer publisher to create an error state
    docker_error_compose_ps_output[4]["Publishers"].pop(2)

    proc_mock.set_output(
        "docker compose ps --format json",
        [json.dumps(docker_error_compose_ps_output)],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("_mock_proc_with_running_localnet")
def test_localnet_status_missing_service(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    # Change to keep algod and indexerdb
    missing_service_compose_ps_output = [compose_ps_output[0].copy(), compose_ps_output[3].copy()]

    proc_mock.set_output(
        "docker compose ps --format json",
        [json.dumps(missing_service_compose_ps_output)],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    assert not httpx_mock.get_request()
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("_mock_proc_with_running_localnet")
def test_localnet_status_failure(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")
    proc_mock.set_output("docker compose ps --format json", output=[json.dumps([])])

    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("proc_mock", "_mock_proc_with_running_localnet")
def test_localnet_status_no_existing_definition(app_dir_mock: AppDirs) -> None:
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_status_without_docker(proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on("docker compose version")

    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_status_without_docker_compose(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_status_without_docker_engine_running(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output)


class DockerServicePublisher(TypedDict):
    URL: str
    TargetPort: int
    PublishedPort: int
    Protocol: str


class DockerServiceInfo(TypedDict):
    ID: str
    Name: str
    Image: str
    Command: str
    Project: str
    Service: str
    Created: int
    State: str
    Status: str
    Health: str
    ExitCode: int
    Publishers: list[DockerServicePublisher]


compose_ps_output: list[DockerServiceInfo] = [
    {
        "ID": "e900c9dfe5e4676ca7fb3ac38cbee366ca5429ae447222282b64c059f5727a47",
        "Name": "algokit_algod",
        "Image": "algorand/algod:latest",
        "Command": "/node/run/run.sh",
        "Project": "algokit_sandbox",
        "Service": "algod",
        "Created": 1701664778,
        "State": "running",
        "Status": "",
        "Health": "",
        "ExitCode": 0,
        "Publishers": [
            {"URL": "", "TargetPort": 4160, "PublishedPort": 0, "Protocol": "tcp"},
            {"URL": "", "TargetPort": 9100, "PublishedPort": 0, "Protocol": "tcp"},
            {"URL": "0.0.0.0", "TargetPort": 9392, "PublishedPort": 9392, "Protocol": "tcp"},
        ],
    },
    {
        "ID": "2ba986bf8539527dbc1f2c3e9d8f83e834099ffea30d31f341691b172748464f",
        "Name": "algokit_conduit",
        "Image": "makerxstudio/conduit-localnet-importer:latest",
        "Command": "docker-entrypoint.sh",
        "Project": "algokit_sandbox",
        "Service": "conduit",
        "Created": 1701664778,
        "State": "running",
        "Status": "",
        "Health": "",
        "ExitCode": 0,
        "Publishers": [],
    },
    {
        "ID": "fa5b36dddbd112eb8b52ccd4de7db47c55ad49124b0483896a23f6727335cb3d",
        "Name": "algokit_sandbox-indexer-1",
        "Image": "algorand/indexer:latest",
        "Command": "docker-entrypoint.sh daemon --enable-all-parameters",
        "Project": "algokit_sandbox",
        "Service": "indexer",
        "Created": 1701664778,
        "State": "running",
        "Status": "",
        "Health": "",
        "ExitCode": 0,
        "Publishers": [],
    },
    {
        "ID": "f3a0bf6fe1e1fcbff96b88f39e30bcadab4c1792234c970d654b7a34fb71e1d7",
        "Name": "algokit_postgres",
        "Image": "postgres:13-alpine",
        "Command": "docker-entrypoint.sh postgres",
        "Project": "algokit_sandbox",
        "Service": "indexer-db",
        "Created": 1701664778,
        "State": "running",
        "Status": "",
        "Health": "",
        "ExitCode": 0,
        "Publishers": [{"URL": "0.0.0.0", "TargetPort": 5432, "PublishedPort": 5443, "Protocol": "tcp"}],
    },
    {
        "ID": "6508be103d216ad8b36f53f85053adbd5cef540f50349e62bc9a57a3526b48a9",
        "Name": "algokit_sandbox_proxy",
        "Image": "nginx:1.27.0-alpine",
        "Command": "docker-entrypoint.sh",
        "Project": "algokit_sandbox",
        "Service": "proxy",
        "Created": 1701664778,
        "State": "running",
        "Status": "",
        "Health": "",
        "ExitCode": 0,
        "Publishers": [
            {"URL": "0.0.0.0", "TargetPort": 4001, "PublishedPort": 4001, "Protocol": "tcp"},
            {"URL": "0.0.0.0", "TargetPort": 4002, "PublishedPort": 4002, "Protocol": "tcp"},
            {"URL": "0.0.0.0", "TargetPort": 8980, "PublishedPort": 8980, "Protocol": "tcp"},
        ],
    },
]
