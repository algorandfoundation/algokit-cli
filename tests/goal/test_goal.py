from subprocess import CompletedProcess

from pytest_mock import MockerFixture
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


def test_goal_help():
    result = invoke("goal -h")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_no_args(proc_mock: ProcMock, mocker: MockerFixture):
    result = invoke("goal")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_console(proc_mock: ProcMock, mocker: MockerFixture):
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("goal --console")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_console_failed(proc_mock: ProcMock, mocker: MockerFixture):
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 1, "STDOUT+STDERR"
    )

    result = invoke("goal --console")

    assert result.exit_code == 1
    verify(result.output)


def test_goal_simple_args(proc_mock: ProcMock):
    result = invoke("goal account list")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_complex_args(proc_mock: ProcMock):
    result = invoke("goal account export -a RKTAZY2ZLKUJBHDVVA3KKHEDK7PRVGIGOZAUUIZBNK2OEP6KQGEXKKUYUY")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_start_without_docker(proc_mock: ProcMock):
    proc_mock.should_fail_on("docker version")

    result = invoke("goal")

    assert result.exit_code == 1
    verify(result.output)


def test_goal_start_without_docker_engine_running(proc_mock: ProcMock):
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("goal")

    assert result.exit_code == 1
    verify(result.output)
