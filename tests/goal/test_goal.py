import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest
from pytest_mock import MockerFixture

from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.fixture()
def cwd(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("cwd")


@pytest.fixture()
def mocked_goal_mount_path(cwd: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mocked_goal_mount_path = cwd / "goal_mount"
    mocked_goal_mount_path.mkdir()
    monkeypatch.setattr("algokit.cli.goal.get_volume_mount_path_local", lambda: cwd / "goal_mount")


@pytest.fixture()
def create_input_file(cwd: Path) -> None:
    (cwd / "approval.teal").write_text(
        """
#pragma version 8
int 1
return
""",
        encoding="utf-8",
    )


@pytest.fixture()
def create_input_file2(cwd: Path) -> None:
    (cwd / "approval2.teal").write_text(
        """
#pragma version 8
int 1
return
""",
        encoding="utf-8",
    )


def dump_file(cwd: Path) -> None:
    (cwd / "approval.compiled").write_text(
        """
I AM COMPILED!
""",
        encoding="utf-8",
    )


def dump_file2(cwd: Path) -> None:
    (cwd / "balance_record.json").write_text(
        """
I AM COMPILED!
""",
        encoding="utf-8",
    )


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


@pytest.mark.usefixtures("proc_mock", "mocked_goal_mount_path", "create_input_file")
def test_goal_simple_args_with_input_file(
    proc_mock: ProcMock,
) -> None:
    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_algod",
        "goal",
        "clerk",
        "group",
        "/root/goal_mount/approval.teal",
    ]

    # TODO: set real goal output expectation
    proc_mock.set_output(expected_arguments, output=["File compiled"])
    result = invoke("goal clerk group approval.teal")

    assert proc_mock.called[1].command[9] == "/root/goal_mount/approval.teal"
    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock", "cwd", "mocked_goal_mount_path", "dump_file2")
def test_goal_simple_args_with_output_file(proc_mock: ProcMock, cwd: Path) -> None:
    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_algod",
        "goal",
        "account",
        "dump",
        "-o",
        "/root/goal_mount/balance_record.json",
    ]

    # TODO: set real goal output expectation
    proc_mock.set_output(expected_arguments, output=["File compiled"], side_effect=dump_file2(cwd))
    result = invoke("goal account dump -o balance_record.json")

    assert proc_mock.called[1].command[10] == "/root/goal_mount/balance_record.json"
    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock", "cwd", "mocked_goal_mount_path", "create_input_file")
def test_goal_simple_args_with_input_output_files(
    proc_mock: ProcMock,
    cwd: Path,
    mocked_goal_mount_path: Path,
) -> None:
    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_algod",
        "goal",
        "clerk",
        "compile",
        "/root/goal_mount/approval.teal",
        "-o",
        "/root/goal_mount/approval.compiled",
    ]

    # TODO: set real goal output expectation
    proc_mock.set_output(expected_arguments, output=["File compiled"], side_effect=dump_file(cwd))

    result = invoke("goal clerk compile approval.teal -o approval.compiled", cwd=cwd)

    assert proc_mock.called[1].command[9] == "/root/goal_mount/approval.teal"
    assert proc_mock.called[1].command[11] == "/root/goal_mount/approval.compiled"

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock", "cwd", "mocked_goal_mount_path", "create_input_file", "create_input_file2")
def test_goal_simple_args_with_multiple_input_output_files(
    proc_mock: ProcMock,
    cwd: Path,
) -> None:
    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_algod",
        "goal",
        "clerk",
        "compile",
        "/root/goal_mount/approval.teal",
        "/root/goal_mount/approval2.teal",
        "-o",
        "/root/goal_mount/approval.compiled",
    ]

    proc_mock.set_output(expected_arguments, output=["File compiled"], side_effect=dump_file(cwd))
    result = invoke("goal clerk compile approval.teal approval2.teal -o approval.compiled", cwd=cwd)

    assert proc_mock.called[1].command[9] == "/root/goal_mount/approval.teal"
    assert proc_mock.called[1].command[10] == "/root/goal_mount/approval2.teal"
    assert proc_mock.called[1].command[12] == "/root/goal_mount/approval.compiled"
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
