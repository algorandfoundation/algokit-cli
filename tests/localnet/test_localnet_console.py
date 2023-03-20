from subprocess import CompletedProcess

from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def test_goal_console(proc_mock: ProcMock, mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("localnet console")

    assert result.exit_code == 0
    verify(result.output)
