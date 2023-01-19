from subprocess import CompletedProcess

from pytest_mock import MockerFixture
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


def test_goal_console(proc_mock: ProcMock, mocker: MockerFixture):
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("localnet console")

    assert result.exit_code == 0
    verify(result.output)
