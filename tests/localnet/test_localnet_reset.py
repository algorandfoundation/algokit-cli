import json

import pytest

from algokit.core.sandbox import get_algod_network_template, get_config_json, get_docker_compose_yml, get_proxy_config
from tests import get_combined_verify_output
from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.mark.usefixtures("proc_mock", "_health_success", "_mock_proc_with_running_localnet")
def test_localnet_reset_without_existing_sandbox(app_dir_mock: AppDirs) -> None:
    result = invoke("localnet reset")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(
            result.output.replace("\\\\", "\\")
            .replace(str(app_dir_mock.app_config_dir), "{app_config}")
            .replace("\\", "/"),
            "{app_config}/sandbox/docker-compose.yml",
            (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_reset_with_existing_sandbox_with_out_of_date_config(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("out of date config")
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text("out of date config")

    result = invoke("localnet reset")

    assert result.exit_code == 0
    verify(
        "\n".join(
            [
                result.output.replace("\\\\", "\\")
                .replace(str(app_dir_mock.app_config_dir), "{app_config}")
                .replace("\\", "/"),
                "{app_config}/sandbox/docker-compose.yml",
                (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
                "{app_config}/sandbox/algod_config.json",
                (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").read_text(),
            ]
        )
    )


@pytest.mark.usefixtures("proc_mock", "_health_success", "_localnet_up_to_date", "_mock_proc_with_running_localnet")
def test_localnet_reset_with_existing_sandbox_with_up_to_date_config(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text(get_config_json())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_network_template.json").write_text(get_algod_network_template())
    (app_dir_mock.app_config_dir / "sandbox" / "nginx.conf").write_text(get_proxy_config())

    result = invoke("localnet reset")

    assert result.exit_code == 0
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("proc_mock", "_health_success")
def test_localnet_reset_with_named_sandbox_config(proc_mock: ProcMock, app_dir_mock: AppDirs) -> None:
    compose_file_path = str(app_dir_mock.app_config_dir / "sandbox_test" / "docker-compose.yml")
    proc_mock.set_output(
        "docker compose ls --format json --filter name=algokit_sandbox*",
        [json.dumps([{"Name": "algokit_sandbox", "Status": "running", "ConfigFiles": compose_file_path}])],
    )
    (app_dir_mock.app_config_dir / "sandbox_test").mkdir()
    (app_dir_mock.app_config_dir / "sandbox_test" / "docker-compose.yml").write_text(
        get_docker_compose_yml(name="algokit_sandbox_test")
    )
    (app_dir_mock.app_config_dir / "sandbox_test" / "algod_config.json").write_text(get_config_json())
    (app_dir_mock.app_config_dir / "sandbox_test" / "algod_network_template.json").write_text(
        get_algod_network_template()
    )
    (app_dir_mock.app_config_dir / "sandbox_test" / "nginx.conf").write_text(get_proxy_config())

    result = invoke("localnet reset")

    assert result.exit_code == 0
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures(
    "proc_mock", "_health_success", "_mock_proc_with_running_localnet", "_mock_proc_with_running_localnet"
)
def test_localnet_reset_with_existing_sandbox_with_up_to_date_config_with_pull(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text(get_config_json())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_network_template.json").write_text(get_algod_network_template())
    (app_dir_mock.app_config_dir / "sandbox" / "nginx.conf").write_text(get_proxy_config())

    result = invoke("localnet reset --update")

    assert result.exit_code == 0
    verify(
        result.output.replace("\\\\", "\\").replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/")
    )


@pytest.mark.usefixtures("app_dir_mock", "_mock_proc_with_running_localnet")
def test_localnet_reset_without_docker(proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on("docker compose version")

    result = invoke("localnet reset")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock", "_mock_proc_with_running_localnet")
def test_localnet_reset_without_docker_compose(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker compose version")

    result = invoke("localnet reset")

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.usefixtures("app_dir_mock", "_mock_proc_with_running_localnet")
def test_localnet_reset_without_docker_engine_running(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("localnet reset")

    assert result.exit_code == 1
    verify(result.output)
