import json

import httpx
import pytest
from algokit.core.sandbox import (
    ALGOD_HEALTH_URL,
    ALGORAND_IMAGE,
    INDEXER_IMAGE,
    get_algod_network_template,
    get_config_json,
    get_docker_compose_yml,
    get_proxy_config,
)
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests import get_combined_verify_output
from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.fixture()
def _localnet_out_of_date(proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    arg = "{{range .RepoDigests}}{{println .}}{{end}}"
    proc_mock.set_output(
        ["docker", "image", "inspect", ALGORAND_IMAGE, "--format", arg],
        ["tag@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"],
    )

    proc_mock.set_output(
        ["docker", "image", "inspect", INDEXER_IMAGE, "--format", arg],
        ["tag@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"],
    )

    httpx_mock.add_response(
        url="https://registry.hub.docker.com/v2/repositories/algorand/indexer/tags/latest",
        json={
            "digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        },
    )

    httpx_mock.add_response(
        url="https://registry.hub.docker.com/v2/repositories/algorand/algod/tags/latest",
        json={
            "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        },
    )


@pytest.fixture()
def _localnet_img_check_cmd_error(proc_mock: ProcMock) -> None:
    arg = "{{range .RepoDigests}}{{println .}}{{end}}"
    proc_mock.should_fail_on(["docker", "image", "inspect", ALGORAND_IMAGE, "--format", arg])
    proc_mock.should_fail_on(["docker", "image", "inspect", INDEXER_IMAGE, "--format", arg])


@pytest.mark.usefixtures("_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start(app_dir_mock: AppDirs) -> None:
    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_up_to_date")
def test_localnet_start_with_name(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.set_output(
        "docker compose ls --format json --filter name=algokit_sandbox*",
        [
            json.dumps(
                [
                    {
                        "Name": "algokit_sandbox_test",
                        "Status": "running",
                        "ConfigFiles": "sandbox_test/docker-compose.yml",
                    }
                ]
            )
        ],
    )
    result = invoke("localnet start --name test")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox_test/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox_test" / "docker-compose.yml").read_text(),
        )
    )


@pytest.mark.usefixtures("proc_mock", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_health_failure(app_dir_mock: AppDirs, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.RemoteProtocolError("No response"), url=ALGOD_HEALTH_URL)
    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


@pytest.mark.usefixtures("proc_mock", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_health_bad_status(app_dir_mock: AppDirs, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=500, url=ALGOD_HEALTH_URL)
    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


@pytest.mark.usefixtures("_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_failure(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker compose up")

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_up_to_date_definition(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text(get_config_json())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_network_template.json").write_text(get_algod_network_template())
    (app_dir_mock.app_config_dir / "sandbox" / "nginx.conf").write_text(get_proxy_config())

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_out_of_date_definition(app_dir_mock: AppDirs, mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.sandbox.ComposeSandbox.is_algod_dev_mode", return_value=True)

    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("out of date config")
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text("out of date config")
    (app_dir_mock.app_config_dir / "sandbox" / "algod_network_template.json").write_text("out of date config")

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(
        "\n".join(
            [
                result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
                "{app_config}/sandbox/docker-compose.yml",
                (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
                "{app_config}/sandbox/algod_config.json",
                (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").read_text(),
                "{app_config}/sandbox/algod_network_template.json",
                (app_dir_mock.app_config_dir / "sandbox" / "algod_network_template.json").read_text(),
            ]
        )
    )


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_out_of_date_definition_and_missing_config(app_dir_mock: AppDirs, mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.sandbox.ComposeSandbox.is_algod_dev_mode", return_value=True)

    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("out of date config")

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(
        "\n".join(
            [
                result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
                "{app_config}/sandbox/docker-compose.yml",
                (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
            ]
        )
    )


@pytest.mark.usefixtures("app_dir_mock", "_mock_proc_with_running_localnet")
def test_localnet_start_without_docker(proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on("docker compose version")

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock", "_mock_proc_with_running_localnet")
def test_localnet_start_without_docker_compose(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock", "_mock_proc_with_running_localnet")
def test_localnet_start_without_docker_engine_running(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock", "_mock_proc_with_running_localnet")
def test_localnet_start_with_old_docker_compose_version(proc_mock: ProcMock) -> None:
    proc_mock.set_output("docker compose version --format json", [json.dumps({"version": "v2.2.1"})])

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_with_unparseable_docker_compose_version(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.set_output("docker compose version --format json", [json.dumps({"version": "v2.5-dev123"})])

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures("_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_with_gitpod_docker_compose_version(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.set_output("docker compose version --format json", [json.dumps({"version": "v2.10.0-gitpod.0"})])

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_out_of_date", "_mock_proc_with_running_localnet")
def test_localnet_start_out_date(app_dir_mock: AppDirs) -> None:
    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures(
    "proc_mock", "_health_success", "_localnet_img_check_cmd_error", "_mock_proc_with_running_localnet"
)
def test_localnet_img_check_cmd_error(app_dir_mock: AppDirs) -> None:
    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_with_custom_config_dir(tmp_path_factory: pytest.TempPathFactory) -> None:
    custom_config_dir = tmp_path_factory.mktemp("custom_config")
    result = invoke(f"localnet start --config-dir {str(custom_config_dir.absolute()).replace("\\", r"\\")}")

    print(result.output.splitlines())  # noqa: T201
    assert result.exit_code == 0
    assert custom_config_dir.exists()
    assert (custom_config_dir / "sandbox").exists()
    assert (custom_config_dir / "sandbox" / "docker-compose.yml").exists()
    assert (custom_config_dir / "sandbox" / "algod_network_template.json").exists()
    assert (custom_config_dir / "sandbox" / "algod_config.json").exists()
    assert (custom_config_dir / "sandbox" / "nginx.conf").exists()


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_start_with_no_dev_mode(app_dir_mock: AppDirs) -> None:
    result = invoke("localnet start --no-dev")

    assert result.exit_code == 0
    # Verify that DevMode is set to false in the algod_network_template.json
    network_template = json.loads(
        (app_dir_mock.app_config_dir / "sandbox" / "algod_network_template.json")
        .read_text()
        .replace("NUM_ROUNDS", '"NUM_ROUNDS"')
    )
    assert not network_template["Genesis"]["DevMode"]
