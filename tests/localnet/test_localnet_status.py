import json

import httpx
from pytest_httpx import HTTPXMock
from utils.app_dir_mock import AppDirs
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


def test_localnet_status_successful(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock):
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
        [
            json.dumps(
                [
                    {
                        "ID": "90ce27e631e4d0b048322abd01a9e68e4c899b936ad4e4e3106ad5d9f774a189",
                        "Name": "algokit_algod",
                        "Command": "start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "algod",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 4001, "PublishedPort": 4001, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 4002, "PublishedPort": 4002, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 9392, "PublishedPort": 9392, "Protocol": "tcp"},
                        ],
                    },
                    {
                        "ID": "d3a74173d552ac388643ee65c9c6aa4c1864cb1442d0423d62bd95c468ac4b97",
                        "Name": "algokit_indexer",
                        "Command": "/tmp/start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "indexer",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 8980, "PublishedPort": 8980, "Protocol": "tcp"}
                        ],
                    },
                    {
                        "ID": "9e66aca1cd3542446e7b88f0701122a90f388308f7de0b57b6e2d843b3da9026",
                        "Name": "algokit_postgres",
                        "Command": "docker-entrypoint.sh postgres",
                        "Project": "algokit_sandbox",
                        "Service": "indexer-db",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [{"URL": "", "TargetPort": 5432, "PublishedPort": 0, "Protocol": "tcp"}],
                    },
                ]
            )
        ],
    )
    result = invoke("localnet status")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_status_http_error(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock):
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
        [
            json.dumps(
                [
                    {
                        "ID": "00e93d3db91d964d1b2bcf444c938140dc6b43398380374eaac8510f45381973",
                        "Name": "algokit_algod",
                        "Command": "start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "algod",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 4001, "PublishedPort": 4001, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 4002, "PublishedPort": 4002, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 9392, "PublishedPort": 9392, "Protocol": "tcp"},
                        ],
                    },
                    {
                        "ID": "a242581a65f7e49d376bff9fd8d2288cdd85a28a264657d73db84dbeef6155b7",
                        "Name": "algokit_indexer",
                        "Command": "/tmp/start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "indexer",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 8980, "PublishedPort": 8980, "Protocol": "tcp"}
                        ],
                    },
                    {
                        "ID": "9e66aca1cd3542446e7b88f0701122a90f388308f7de0b57b6e2d843b3da9026",
                        "Name": "algokit_postgres",
                        "Command": "docker-entrypoint.sh postgres",
                        "Project": "algokit_sandbox",
                        "Service": "indexer-db",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [{"URL": "", "TargetPort": 5432, "PublishedPort": 0, "Protocol": "tcp"}],
                    },
                ]
            )
        ],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_status_unexpected_port(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock):
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

    proc_mock.set_output(
        "docker compose ps --format json",
        [
            json.dumps(
                [
                    {
                        "ID": "00e93d3db91d964d1b2bcf444c938140dc6b43398380374eaac8510f45381973",
                        "Name": "algokit_algod",
                        "Command": "start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "algod",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 4001, "PublishedPort": 4001, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 4002, "PublishedPort": 4002, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 9392, "PublishedPort": 9392, "Protocol": "tcp"},
                        ],
                    },
                    {
                        "ID": "a242581a65f7e49d376bff9fd8d2288cdd85a28a264657d73db84dbeef6155b7",
                        "Name": "algokit_indexer",
                        "Command": "/tmp/start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "indexer",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 1234, "PublishedPort": 1234, "Protocol": "tcp"}
                        ],
                    },
                    {
                        "ID": "9e66aca1cd3542446e7b88f0701122a90f388308f7de0b57b6e2d843b3da9026",
                        "Name": "algokit_postgres",
                        "Command": "docker-entrypoint.sh postgres",
                        "Project": "algokit_sandbox",
                        "Service": "indexer-db",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [{"URL": "", "TargetPort": 5432, "PublishedPort": 0, "Protocol": "tcp"}],
                    },
                ]
            )
        ],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_status_service_not_started(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    httpx_mock.add_response(
        url="http://localhost:8980/health", json={"round": 1, "errors": ["error"], "version": "v1.0"}
    )

    proc_mock.set_output(
        "docker compose ps --format json",
        [
            json.dumps(
                [
                    {
                        "ID": "00e93d3db91d964d1b2bcf444c938140dc6b43398380374eaac8510f45381973",
                        "Name": "algokit_algod",
                        "Command": "start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "algod",
                        "State": "stopped",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 4001, "PublishedPort": 4001, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 4002, "PublishedPort": 4002, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 9392, "PublishedPort": 9392, "Protocol": "tcp"},
                        ],
                    },
                    {
                        "ID": "a242581a65f7e49d376bff9fd8d2288cdd85a28a264657d73db84dbeef6155b7",
                        "Name": "algokit_indexer",
                        "Command": "/tmp/start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "indexer",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 8980, "PublishedPort": 8980, "Protocol": "tcp"}
                        ],
                    },
                    {
                        "ID": "9e66aca1cd3542446e7b88f0701122a90f388308f7de0b57b6e2d843b3da9026",
                        "Name": "algokit_postgres",
                        "Command": "docker-entrypoint.sh postgres",
                        "Project": "algokit_sandbox",
                        "Service": "indexer-db",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [{"URL": "", "TargetPort": 5432, "PublishedPort": 0, "Protocol": "tcp"}],
                    },
                ]
            )
        ],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_status_docker_error(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock):
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

    proc_mock.set_output(
        "docker compose ps --format json",
        [
            json.dumps(
                [
                    {
                        "ID": "00e93d3db91d964d1b2bcf444c938140dc6b43398380374eaac8510f45381973",
                        "Name": "algokit_algod",
                        "Command": "start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "algod",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 4001, "PublishedPort": 4001, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 4002, "PublishedPort": 4002, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 9392, "PublishedPort": 9392, "Protocol": "tcp"},
                        ],
                    },
                    {
                        "ID": "a242581a65f7e49d376bff9fd8d2288cdd85a28a264657d73db84dbeef6155b7",
                        "Name": "algokit_indexer",
                        "Command": "/tmp/start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "indexer",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [],
                    },
                    {
                        "ID": "9e66aca1cd3542446e7b88f0701122a90f388308f7de0b57b6e2d843b3da9026",
                        "Name": "algokit_postgres",
                        "Command": "docker-entrypoint.sh postgres",
                        "Project": "algokit_sandbox",
                        "Service": "indexer-db",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [{"URL": "", "TargetPort": 5432, "PublishedPort": 0, "Protocol": "tcp"}],
                    },
                ]
            )
        ],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_status_missing_service(app_dir_mock: AppDirs, proc_mock: ProcMock, httpx_mock: HTTPXMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    proc_mock.set_output(
        "docker compose ps --format json",
        [
            json.dumps(
                [
                    {
                        "ID": "00e93d3db91d964d1b2bcf444c938140dc6b43398380374eaac8510f45381973",
                        "Name": "algokit_algod",
                        "Command": "start.sh",
                        "Project": "algokit_sandbox",
                        "Service": "algod",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [
                            {"URL": "0.0.0.0", "TargetPort": 4001, "PublishedPort": 4001, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 4002, "PublishedPort": 4002, "Protocol": "tcp"},
                            {"URL": "0.0.0.0", "TargetPort": 9392, "PublishedPort": 9392, "Protocol": "tcp"},
                        ],
                    },
                    {
                        "ID": "9e66aca1cd3542446e7b88f0701122a90f388308f7de0b57b6e2d843b3da9026",
                        "Name": "algokit_postgres",
                        "Command": "docker-entrypoint.sh postgres",
                        "Project": "algokit_sandbox",
                        "Service": "indexer-db",
                        "State": "running",
                        "Health": "",
                        "ExitCode": 0,
                        "Publishers": [{"URL": "", "TargetPort": 5432, "PublishedPort": 0, "Protocol": "tcp"}],
                    },
                ]
            )
        ],
    )
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_status_failure(app_dir_mock: AppDirs, proc_mock: ProcMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")
    proc_mock.should_bad_exit_on("docker compose stop")

    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_status_no_existing_definition(app_dir_mock: AppDirs, proc_mock: ProcMock):
    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_status_without_docker(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_fail_on("docker compose version")

    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output)


def test_localnet_status_without_docker_compose(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output)


def test_localnet_status_without_docker_engine_running(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("localnet status")

    assert result.exit_code == 1
    verify(result.output)
