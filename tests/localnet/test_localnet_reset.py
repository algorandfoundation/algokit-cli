from algokit.core.sandbox import get_docker_compose_yml

from tests import get_combined_verify_output
from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def test_localnet_reset_without_existing_sandbox(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    result = invoke("localnet reset")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


def test_localnet_reset_with_existing_sandbox_with_out_of_date_config(
    app_dir_mock: AppDirs, proc_mock: ProcMock
) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("out of date config")

    result = invoke("localnet reset")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(
            result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


def test_localnet_reset_with_existing_sandbox_with_up_to_date_config(
    app_dir_mock: AppDirs, proc_mock: ProcMock
) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())

    result = invoke("localnet reset")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_reset_with_existing_sandbox_with_up_to_date_config_no_pull(
    app_dir_mock: AppDirs, proc_mock: ProcMock
) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())

    result = invoke("localnet reset --no-update")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_localnet_reset_without_docker(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on("docker compose version")

    result = invoke("localnet reset")

    assert result.exit_code == 1
    verify(result.output)


def test_localnet_reset_without_docker_compose(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("localnet reset")

    assert result.exit_code == 1
    verify(result.output)


def test_localnet_reset_without_docker_engine_running(app_dir_mock: AppDirs, proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("localnet reset")

    assert result.exit_code == 1
    verify(result.output)
