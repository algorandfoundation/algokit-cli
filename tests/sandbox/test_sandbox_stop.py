from approvaltests import verify  # type: ignore
from utils.app_dir_mock import AppDirs
from utils.click_invoker import invoke
from utils.exec_mock import ExecMock


def get_verify_output(stdout: str, additional_name: str, additional_output: str) -> str:
    return f"""{stdout}----
{additional_name}:
----
{additional_output}"""


def test_sandbox_stop(app_dir_mock: AppDirs, exec_mock: ExecMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    result = invoke("sandbox stop")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_stop_failure(app_dir_mock: AppDirs, exec_mock: ExecMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")
    exec_mock.should_bad_exit_on("docker compose stop")

    result = invoke("sandbox stop")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_stop_no_existing_definition(app_dir_mock: AppDirs, exec_mock: ExecMock):
    result = invoke("sandbox stop")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_stop_without_docker(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_fail_on("docker compose version")

    result = invoke("sandbox stop")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_stop_without_docker_compose(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_bad_exit_on("docker compose version")

    result = invoke("sandbox stop")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_stop_without_docker_engine_running(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_bad_exit_on("docker version")

    result = invoke("sandbox stop")

    assert result.exit_code == 1
    verify(result.output)
