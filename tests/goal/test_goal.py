import json
from subprocess import CompletedProcess

import pytest
from pytest_mock import MockerFixture

from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def test_goal_help() -> None:
    result = invoke("goal -h")

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_goal_no_args() -> None:
    result = invoke("goal")

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_goal_console(mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("goal --console")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_console_failed(app_dir_mock: AppDirs, proc_mock: ProcMock, mocker: MockerFixture) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()

    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 1, "STDOUT+STDERR"
    )

    proc_mock.set_output(
        ["docker", "compose", "ps", "algod", "--format", "json"],
        output=[json.dumps([{"Name": "algokit_algod", "State": "running"}])],
    )

    result = invoke("goal --console")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_goal_console_failed_algod_not_created(
    app_dir_mock: AppDirs, proc_mock: ProcMock, mocker: MockerFixture
) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()

    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 1, "bad args to goal"
    )

    proc_mock.set_output(["docker", "compose", "ps", "algod", "--format", "json"], output=[json.dumps([])])

    result = invoke("goal --console")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


@pytest.mark.usefixtures("proc_mock")
def test_goal_simple_args() -> None:
    result = invoke("goal account list")

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_goal_complex_args() -> None:
    result = invoke("goal account export -a RKTAZY2ZLKUJBHDVVA3KKHEDK7PRVGIGOZAUUIZBNK2OEP6KQGEXKKUYUY")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_start_without_docker(proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on("docker version")

    result = invoke("goal")

    assert result.exit_code == 1
    verify(result.output)


def test_goal_start_without_docker_engine_running(proc_mock: ProcMock) -> None:
    proc_mock.should_bad_exit_on("docker version")

    result = invoke("goal")

    assert result.exit_code == 1
    verify(result.output)
