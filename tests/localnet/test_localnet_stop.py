import json

import pytest

from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.mark.usefixtures("proc_mock", "_mock_proc_with_running_localnet")
def test_localnet_stop(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text("existing")

    result = invoke("localnet stop")

    assert result.exit_code == 0
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


def test_localnet_stop_with_name(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox_test").mkdir()
    (app_dir_mock.app_config_dir / "sandbox_test" / "docker-compose.yml").write_text("existing")
    (app_dir_mock.app_config_dir / "sandbox_test" / "algod_config.json").write_text("existing")
    proc_mock.set_output(
        "docker compose ls --format json --filter name=algokit_sandbox*",
        [
            json.dumps(
                [
                    {
                        "Name": "algokit_sandbox_test",
                        "Status": "running",
                        "ConfigFiles": str(app_dir_mock.app_config_dir / "sandbox_test" / "docker-compose.yml"),
                    }
                ]
            )
        ],
    )
    result = invoke("localnet stop")

    assert result.exit_code == 0
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("_mock_proc_with_running_localnet")
def test_localnet_stop_failure(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text("existing")
    proc_mock.should_bad_exit_on("docker compose stop")

    result = invoke("localnet stop")

    assert result.exit_code == 1
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("proc_mock", "_mock_proc_with_running_localnet")
def test_localnet_stop_no_existing_definition(app_dir_mock: AppDirs) -> None:
    result = invoke("localnet stop")

    assert result.exit_code == 0
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_stop_without_docker(proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on("docker compose version")

    result = invoke("localnet stop")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_stop_without_docker_compose(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("localnet stop")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_stop_without_docker_engine_running(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("localnet stop")

    assert result.exit_code == 1
    verify(result.output)
