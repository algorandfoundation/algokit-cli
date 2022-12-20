from utils.app_dir_mock import AppDirs
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


def test_sandbox_stop(app_dir_mock: AppDirs, proc_mock: ProcMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    result = invoke("sandbox stop")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_stop_failure(app_dir_mock: AppDirs, proc_mock: ProcMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")
    proc_mock.should_bad_exit_on("docker compose stop")

    result = invoke("sandbox stop")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_stop_no_existing_definition(app_dir_mock: AppDirs, proc_mock: ProcMock):
    result = invoke("sandbox stop")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_stop_without_docker(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_fail_on("docker compose version")

    result = invoke("sandbox stop")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_stop_without_docker_compose(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("sandbox stop")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_stop_without_docker_engine_running(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("sandbox stop")

    assert result.exit_code == 1
    verify(result.output)
