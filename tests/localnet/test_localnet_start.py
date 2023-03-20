import json

import pytest
from algokit.core.sandbox import get_docker_compose_yml

from tests import get_combined_verify_output
from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.mark.usefixtures("proc_mock")
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


def test_localnet_start_failure(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker compose up")

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures("proc_mock")
def test_localnet_start_up_to_date_definition(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures("proc_mock")
def test_localnet_start_out_of_date_definition(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("out of date config")

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_start_without_docker(proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on("docker compose version")

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_start_without_docker_compose(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_start_without_docker_engine_running(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock")
def test_localnet_start_with_old_docker_compose_version(proc_mock: ProcMock) -> None:
    proc_mock.set_output("docker compose version --format json", [json.dumps({"version": "v2.2.1"})])

    result = invoke("localnet start")

    assert result.exit_code == 1
    verify(result.output)


def test_localnet_start_with_unparseable_docker_compose_version(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.set_output("docker compose version --format json", [json.dumps({"version": "v2.5-dev123"})])

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_start_with_gitpod_docker_compose_version(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.set_output("docker compose version --format json", [json.dumps({"version": "v2.10.0-gitpod.0"})])

    result = invoke("localnet start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))
