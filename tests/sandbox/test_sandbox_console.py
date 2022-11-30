from subprocess import CompletedProcess

from approvaltests import verify  # type: ignore
from pytest_mock import MockerFixture
from utils.click_invoker import invoke
from utils.exec_mock import ExecMock


def test_goal_console(exec_mock: ExecMock, mocker: MockerFixture):
    mocker.patch("algokit.core.exec.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("sandbox console")

    assert result.exit_code == 0
    verify(result.output)
