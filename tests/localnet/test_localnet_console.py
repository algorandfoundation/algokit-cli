import json
from subprocess import CompletedProcess

import pytest
from algokit.core.sandbox import get_algod_network_template, get_config_json, get_docker_compose_yml
from pytest_mock import MockerFixture

from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def test_goal_console(
    mocker: MockerFixture, tmp_path_factory: pytest.TempPathFactory, app_dir_mock: AppDirs, proc_mock: ProcMock
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mocked_goal_mount = cwd / "goal_mount"
    mocked_goal_mount.mkdir()
    mocker.patch("algokit.cli.goal.get_volume_mount_path_local").return_value = mocked_goal_mount

    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text(get_config_json())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_network_template.json").write_text(get_algod_network_template())

    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )
    proc_mock.set_output(
        "docker compose ls --format json --filter name=algokit_*",
        [
            json.dumps(
                [
                    {
                        "Name": "algokit_sandbox",
                        "Status": "running",
                        "ConfigFiles": "test/sandbox_test/docker-compose.yml",
                    }
                ]
            )
        ],
    )

    result = invoke("localnet console")

    assert result.exit_code == 0
    verify(result.output)
