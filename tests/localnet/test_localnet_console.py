from subprocess import CompletedProcess

import pytest
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.mark.usefixtures("proc_mock")
def test_goal_console(mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("localnet console")

    assert result.exit_code == 0
    verify(result.output)
