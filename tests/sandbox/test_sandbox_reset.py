from algokit.core.sandbox import get_docker_compose_yml
from approvaltests import verify  # type: ignore
from utils.app_dir_mock import AppDirs
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


def get_verify_output(stdout: str, additional_name: str, additional_output: str) -> str:
    return f"""{stdout}----
{additional_name}:
----
{additional_output}"""


def test_sandbox_reset_without_existing_sandbox(app_dir_mock: AppDirs, proc_mock: ProcMock):
    result = invoke("sandbox reset")

    assert result.exit_code == 0
    verify(
        get_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


def test_sandbox_reset_with_existing_sandbox_with_out_of_date_config(app_dir_mock: AppDirs, proc_mock: ProcMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("out of date config")

    result = invoke("sandbox reset")

    assert result.exit_code == 0
    verify(
        get_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


def test_sandbox_reset_with_existing_sandbox_with_up_to_date_config(app_dir_mock: AppDirs, proc_mock: ProcMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())

    result = invoke("sandbox reset")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_reset_with_existing_sandbox_with_up_to_date_config_no_pull(app_dir_mock: AppDirs, proc_mock: ProcMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())

    result = invoke("sandbox reset --no-update")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_reset_without_docker(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_fail_on("docker compose version")

    result = invoke("sandbox reset")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_reset_without_docker_compose(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("sandbox reset")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_reset_without_docker_engine_running(app_dir_mock: AppDirs, proc_mock: ProcMock):
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("sandbox reset")

    assert result.exit_code == 1
    verify(result.output)
