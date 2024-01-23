import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest
from algokit.core.sandbox import ALGOD_HEALTH_URL, get_algod_network_template, get_config_json, get_docker_compose_yml
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock

DUMMY_CONTRACT_TEAL = """\n#pragma version 8\nint 1\nreturn\n"""


def _normalize_output(output: str) -> str:
    return output.replace("\\", "/")


@pytest.fixture()
def _health_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=ALGOD_HEALTH_URL)


@pytest.fixture()
def cwd(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("cwd")


@pytest.fixture()
def mocked_goal_mount_path(cwd: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    mocked_goal_mount = cwd / "goal_mount"
    mocked_goal_mount.mkdir()
    monkeypatch.setattr("algokit.cli.goal.get_volume_mount_path_local", lambda directory_name: cwd / "goal_mount")  # noqa: ARG005
    return mocked_goal_mount


@pytest.fixture()
def _setup_latest_dummy_compose(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text(get_docker_compose_yml())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text(get_config_json())
    (app_dir_mock.app_config_dir / "sandbox" / "algod_network_template.json").write_text(get_algod_network_template())


@pytest.fixture()
def _setup_input_files(cwd: Path, request: pytest.FixtureRequest) -> None:
    files = request.param
    for file in files:
        if "name" in file:
            if "content" in file:
                (cwd / file["name"]).write_text(file["content"], encoding="utf-8")
            else:
                (cwd / file["name"]).touch()

            assert (cwd / file["name"]).exists()


@pytest.fixture()
def _mock_proc_with_running_localnet(proc_mock: ProcMock) -> None:
    proc_mock.set_output("docker compose ls --format json --filter name=algokit_sandbox*", [json.dumps([])])


@pytest.fixture()
def _mock_proc_with_algod_running_state(proc_mock: ProcMock) -> None:
    proc_mock.set_output(
        cmd=["docker", "compose", "ps", "algod", "--format", "json"],
        output=[json.dumps([{"Name": "algokit_sandbox_algod", "State": "running"}])],
    )


def dump_file(cwd: Path) -> None:
    (cwd / "approval.compiled").write_text(
        """
I AM COMPILED!
""",
        encoding="utf-8",
    )


def dump_json_file(cwd: Path) -> None:
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


@pytest.mark.usefixtures(
    "proc_mock",
    "_setup_latest_dummy_compose",
    "mocked_goal_mount_path",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
def test_goal_no_args(app_dir_mock: AppDirs) -> None:
    result = invoke("goal")

    assert result.exit_code == 0
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "proc_mock",
    "_setup_latest_dummy_compose",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
def test_goal_console(mocker: MockerFixture, app_dir_mock: AppDirs) -> None:
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("goal --console")

    assert result.exit_code == 0
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures("_setup_latest_dummy_compose", "_mock_proc_with_running_localnet", "_health_success")
def test_goal_console_algod_not_created(app_dir_mock: AppDirs, proc_mock: ProcMock, mocker: MockerFixture) -> None:
    proc_mock.set_output(["docker", "compose", "ps", "algod", "--format", "json"], output=[json.dumps([])])

    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 0, "STDOUT+STDERR"
    )

    result = invoke("goal --console")

    assert result.exit_code == 0
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "proc_mock",
    "_setup_latest_dummy_compose",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
def test_goal_console_failed(app_dir_mock: AppDirs, mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        ["docker", "exec"], 1, "STDOUT+STDERR"
    )

    result = invoke("goal --console")

    assert result.exit_code == 1
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "proc_mock",
    "_setup_latest_dummy_compose",
    "mocked_goal_mount_path",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
def test_goal_simple_args(app_dir_mock: AppDirs) -> None:
    result = invoke("goal account list")

    assert result.exit_code == 0
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "proc_mock",
    "_setup_latest_dummy_compose",
    "mocked_goal_mount_path",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
def test_goal_complex_args(app_dir_mock: AppDirs) -> None:
    result = invoke("goal account export -a RKTAZY2ZLKUJBHDVVA3KKHEDK7PRVGIGOZAUUIZBNK2OEP6KQGEXKKUYUY")

    assert result.exit_code == 0
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


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


@pytest.mark.usefixtures(
    "_setup_input_files",
    "_setup_latest_dummy_compose",
    "mocked_goal_mount_path",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
@pytest.mark.parametrize("_setup_input_files", [[{"name": "transactions.txt"}]], indirect=True)
def test_goal_simple_args_with_input_file(
    proc_mock: ProcMock,
    cwd: Path,
    app_dir_mock: AppDirs,
) -> None:
    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_sandbox_algod",
        "goal",
        "clerk",
        "group",
    ]

    proc_mock.set_output(expected_arguments, output=["File compiled"])
    result = invoke("goal clerk group transactions.txt", cwd=cwd)

    # Check if the path in command has changed in preprocess step
    assert _normalize_output(proc_mock.called[3].command[9]) == "/root/goal_mount/transactions.txt"

    # Check for the result status
    assert result.exit_code == 0

    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "mocked_goal_mount_path",
    "_setup_latest_dummy_compose",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
def test_goal_simple_args_with_output_file(proc_mock: ProcMock, cwd: Path, app_dir_mock: AppDirs) -> None:
    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_sandbox_algod",
        "goal",
        "account",
        "dump",
    ]

    proc_mock.set_output(
        expected_arguments,
        output=["File compiled"],
        side_effect=dump_json_file,
        side_effect_args={"cwd": cwd},
    )
    result = invoke("goal account dump -o balance_record.json")

    # Check if the path in command has changed in preprocess step
    assert _normalize_output(proc_mock.called[3].command[10]) == "/root/goal_mount/balance_record.json"

    # Check for the result status
    assert result.exit_code == 0

    # Check if the output file is actually created and copied in cwd in postprocess step
    assert (cwd / "balance_record.json").exists()

    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "mocked_goal_mount_path",
    "_setup_input_files",
    "_setup_latest_dummy_compose",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
@pytest.mark.parametrize(
    "_setup_input_files", [[{"name": "approval.teal", "content": DUMMY_CONTRACT_TEAL}]], indirect=True
)
def test_goal_simple_args_with_input_output_files(
    proc_mock: ProcMock,
    cwd: Path,
    app_dir_mock: AppDirs,
) -> None:
    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_sandbox_algod",
        "goal",
        "clerk",
        "compile",
    ]

    proc_mock.set_output(
        expected_arguments, output=["File compiled"], side_effect=dump_file, side_effect_args={"cwd": cwd}
    )

    result = invoke("goal clerk compile approval.teal -o approval.compiled", cwd=cwd)

    # Check if the paths in command have changed in preprocess step
    assert _normalize_output(proc_mock.called[3].command[9]) == "/root/goal_mount/approval.teal"
    assert _normalize_output(proc_mock.called[3].command[11]) == "/root/goal_mount/approval.compiled"

    # Check for the result status
    assert result.exit_code == 0

    # Check if the output file is created and copied in cwd in postprocess step
    assert (cwd / "approval.compiled").exists()
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "mocked_goal_mount_path",
    "_setup_input_files",
    "_setup_latest_dummy_compose",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
@pytest.mark.parametrize(
    "_setup_input_files",
    [
        [
            {"name": "approval1.teal", "content": DUMMY_CONTRACT_TEAL},
            {"name": "approval2.teal", "content": DUMMY_CONTRACT_TEAL},
        ]
    ],
    indirect=True,
)
def test_goal_simple_args_with_multiple_input_output_files(
    proc_mock: ProcMock,
    cwd: Path,
    app_dir_mock: AppDirs,
) -> None:
    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_sandbox_algod",
        "goal",
        "clerk",
        "compile",
    ]

    proc_mock.set_output(
        expected_arguments, output=["File compiled"], side_effect=dump_file, side_effect_args={"cwd": cwd}
    )
    result = invoke("goal clerk compile approval1.teal approval2.teal -o approval.compiled", cwd=cwd)

    # Check if the paths in command have changed in preprocess step
    assert _normalize_output(proc_mock.called[3].command[9]) == "/root/goal_mount/approval1.teal"
    assert _normalize_output(proc_mock.called[3].command[10]) == "/root/goal_mount/approval2.teal"
    assert _normalize_output(proc_mock.called[3].command[12]) == "/root/goal_mount/approval.compiled"

    # Check for the result
    assert result.exit_code == 0

    # Check if the output file is actually created and copied in cwd in postprocess step
    assert (cwd / "approval.compiled").exists()
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "proc_mock",
    "mocked_goal_mount_path",
    "_setup_latest_dummy_compose",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
def test_goal_simple_args_without_file_error(
    cwd: Path,
    app_dir_mock: AppDirs,
) -> None:
    assert not (cwd / "approval.teal").exists()
    result = invoke("goal clerk compile approval.teal -o approval.compiled", cwd=cwd)

    assert result.exit_code == 1
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))


@pytest.mark.usefixtures(
    "_setup_input_files",
    "_setup_latest_dummy_compose",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
@pytest.mark.parametrize(
    "_setup_input_files", [[{"name": "approval.teal", "content": DUMMY_CONTRACT_TEAL}]], indirect=True
)
def test_goal_postprocess_of_command_args(
    proc_mock: ProcMock,
    cwd: Path,
    mocked_goal_mount_path: Path,
) -> None:
    # adding some dummy files to the mocked_goal_mount_path
    (mocked_goal_mount_path / "approval.group").touch()
    (mocked_goal_mount_path / "approval.group.sig").touch()
    (mocked_goal_mount_path / "approval.group.sig.out").touch()

    expected_arguments = [
        "docker",
        "exec",
        "--interactive",
        "--workdir",
        "/root",
        "algokit_sandbox_algod",
        "goal",
        "clerk",
        "compile",
    ]
    proc_mock.set_output(
        expected_arguments,
        output=["File compiled"],
        side_effect=dump_file,
        side_effect_args={"cwd": mocked_goal_mount_path},
    )

    result = invoke("goal clerk compile approval.teal -o approval.compiled", cwd=cwd)
    assert result.exit_code == 0

    # check if the output files are no longer in the goal_mount_path
    assert not (mocked_goal_mount_path / "approval.compiled").exists()

    # check if the input/output file is in the cwd
    assert (cwd / "approval.compiled").exists()
    assert (cwd / "approval.teal").exists()

    # check if the dummy files are still there
    assert (mocked_goal_mount_path / "approval.group").exists()
    assert (mocked_goal_mount_path / "approval.group.sig").exists()
    assert (mocked_goal_mount_path / "approval.group.sig.out").exists()


@pytest.mark.usefixtures(
    "_setup_input_files",
    "_setup_latest_dummy_compose",
    "_mock_proc_with_running_localnet",
    "_mock_proc_with_algod_running_state",
)
@pytest.mark.parametrize("_setup_input_files", [[{"name": "group.gtxn", "content": ""}]], indirect=True)
def test_goal_postprocess_of_single_output_arg_resulting_in_multiple_output_files(
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
        "algokit_sandbox_algod",
        "goal",
        "clerk",
        "split",
    ]

    def dump_files(cwd: Path) -> None:
        (cwd / "group-0.txn").touch()
        (cwd / "group-1.txn").touch()

    proc_mock.set_output(
        expected_arguments,
        output=["Wrote transaction"],
        side_effect=dump_files,
        side_effect_args={"cwd": mocked_goal_mount_path},
    )

    result = invoke("goal clerk split -i group.gtxn -o group.txn", cwd=cwd)
    assert result.exit_code == 0

    # check if the output files are no longer in the goal_mount_path
    assert not (mocked_goal_mount_path / "group-0.txn").exists()
    assert not (mocked_goal_mount_path / "group-1.txn").exists()

    # check if the input/output file is in the cwd
    assert (cwd / "group.gtxn").exists()
    assert (cwd / "group-0.txn").exists()
    assert (cwd / "group-1.txn").exists()


@pytest.mark.usefixtures("proc_mock", "_mock_proc_with_running_localnet")
def test_goal_compose_outdated(
    cwd: Path,
    app_dir_mock: AppDirs,
) -> None:
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("Outdated")
    (app_dir_mock.app_config_dir / "sandbox" / "algod_config.json").write_text("Outdated")

    result = invoke("goal help", cwd=cwd)

    assert result.exit_code == 1

    verify(_normalize_output(result.output))


@pytest.mark.usefixtures("_setup_latest_dummy_compose", "mocked_goal_mount_path", "_mock_proc_with_algod_running_state")
def test_goal_simple_args_on_named_localnet(proc_mock: ProcMock, app_dir_mock: AppDirs) -> None:
    proc_mock.set_output(
        "docker compose ls --format json --filter name=algokit_sandbox*",
        [json.dumps([{"Name": "algokit_test", "Status": "running", "ConfigFiles": "to/test/docker-compose.yml"}])],
    )

    result = invoke("goal account list")

    assert result.exit_code == 0
    verify(_normalize_output(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}")))
