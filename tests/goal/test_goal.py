from approvaltests import verify  # type: ignore
from utils.app_dir_mock import AppDirs
from utils.click_invoker import invoke
from utils.exec_mock import ExecMock


def test_goal_no_args(app_dir_mock: AppDirs, exec_mock: ExecMock):
    result = invoke("goal")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_simple_args(app_dir_mock: AppDirs, exec_mock: ExecMock):
    result = invoke("goal account list")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_complex_args(app_dir_mock: AppDirs, exec_mock: ExecMock):
    result = invoke("goal account export -a RKTAZY2ZLKUJBHDVVA3KKHEDK7PRVGIGOZAUUIZBNK2OEP6KQGEXKKUYUY")

    assert result.exit_code == 0
    verify(result.output)


def test_goal_start_without_docker(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_fail_on("docker version")

    result = invoke("goal")

    assert result.exit_code == 1
    verify(result.output)


def test_goal_start_without_docker_engine_running(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_bad_exit_on("docker version")

    result = invoke("goal")

    assert result.exit_code == 1
    verify(result.output)
