from subprocess import CompletedProcess

import pytest
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.mark.usefixtures(
    "proc_mock",
)
def test_goal_console(mocker: MockerFixture, tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mocked_goal_mount = cwd / "goal_mount"
    mocked_goal_mount.mkdir()
    mocker.patch("algokit.cli.goal.get_volume_mount_path_local").return_value = mocked_goal_mount
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("localnet console")

    assert result.exit_code == 0
    verify(result.output)
