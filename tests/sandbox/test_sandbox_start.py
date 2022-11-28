import json

from approvaltests import verify  # type: ignore
from rdmak.core.sandbox import get_docker_compose_yml
from utils.app_dir_mock import AppDirs
from utils.click_invoker import invoke
from utils.exec_mock import ExecMock


def get_verify_output(stdout: str, additional_name: str, additional_output: str) -> str:
    return f"""{stdout}----
{additional_name}:
----
{additional_output}"""


def test_sandbox_start(app_dir_mock: AppDirs, exec_mock: ExecMock):
    result = invoke("sandbox start")

    assert result.exit_code == 0
    verify(
        get_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


def test_sandbox_start_failure(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_bad_exit_on("docker compose up")

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_start_up_to_date_definition(app_dir_mock: AppDirs, exec_mock: ExecMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())

    result = invoke("sandbox start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_start_out_of_date_definition(app_dir_mock: AppDirs, exec_mock: ExecMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("out of date config")

    result = invoke("sandbox start")

    assert result.exit_code == 0
    verify(
        get_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


def test_sandbox_start_without_docker(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_fail_on("docker compose version")

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_start_without_docker_compose(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_bad_exit_on("docker compose version")

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_start_without_docker_engine_running(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_bad_exit_on("docker version")

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_start_with_old_docker_compose_version(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.set_output("docker compose version --format json", [json.dumps({"version": "v2.2.1"})])

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_start_with_unparseable_docker_compose_version(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.set_output("docker compose version --format json", [json.dumps({"version": "v2.5-dev123"})])

    result = invoke("sandbox start")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))
