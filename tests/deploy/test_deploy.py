import sys
from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.core.conf import ALGOKIT_CONFIG
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def test_algokit_config_empty_array(tmp_path_factory: TempPathFactory) -> None:
    empty_array_config = """
[deploy]
command = []
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(empty_array_config, encoding="utf-8")
    (cwd / ".env").touch()
    result = invoke(["deploy"], cwd=cwd)

    assert result.exit_code != 0
    verify(result.output)


def test_algokit_config_invalid_syntax(tmp_path_factory: TempPathFactory) -> None:
    invalid_config = """
{"dummy": "json"}
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(invalid_config, encoding="utf-8")
    (cwd / ".env").touch()
    result = invoke(["deploy"], cwd=cwd)

    assert result.exit_code != 0
    verify(result.output)


def test_algokit_config_name_overrides(tmp_path_factory: TempPathFactory, proc_mock: ProcMock) -> None:
    python_executable = sys.executable
    config_with_override = """
[deploy]
command = "command_a"

[deploy.localnet]
command = "command_b"

[deploy.testnet]
command = "command_c"
    """.strip()
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_override, encoding="utf-8")
    (cwd / ".env").touch()
    (cwd / ".env.localnet").touch()
    (cwd / ".env.testnet").touch()

    proc_mock.set_output(["command_c"], ["picked testnet"])

    result = invoke(["deploy", "testnet"], cwd=cwd)

    assert result.exit_code == 0
    verify(result.output.replace(python_executable, "<sys.executable>"))


def test_algokit_config_name_no_base(tmp_path_factory: TempPathFactory, proc_mock: ProcMock) -> None:
    python_executable = sys.executable
    config_with_override = """
[deploy.localnet]
command = "command_a"

[deploy.testnet]
command = "command_b"
    """.strip()
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_override, encoding="utf-8")
    (cwd / ".env.localnet").touch()
    (cwd / ".env.testnet").touch()

    proc_mock.set_output(["command_a"], ["picked localnet"])

    result = invoke(["deploy", "localnet"], cwd=cwd)

    assert result.exit_code == 0
    verify(result.output.replace(python_executable, "<sys.executable>"))


def test_command_invocation_and_command_splitting(tmp_path: Path) -> None:
    config_data = """
[deploy]
command = ["not", "used"]
    """.strip()
    (tmp_path / ALGOKIT_CONFIG).write_text(config_data, encoding="utf-8")
    python_executable = sys.executable
    result = invoke(
        [
            "deploy",
            "--command",
            # note: spaces around the string inside print are important,
            # we need to test the usage of shlex.split vs str.split, to handle
            # splitting inside quotes properly
            f"{python_executable} -c 'print(\" test_command_invocation \")'",
        ],
        cwd=tmp_path,
    )
    assert result.exit_code == 0
    verify(result.output.replace(python_executable, "<sys.executable>"))


def test_command_splitting_from_config(tmp_path: Path) -> None:
    python_executable = sys.executable
    # note: spaces around the string inside print are important,
    # we need to test the usage of shlex.split vs str.split, to handle
    # splitting inside quotes properly
    config_data = rf"""
[deploy]
command = "{python_executable} -c 'print(\" test_command_invocation \")'"
    """.strip()
    (tmp_path / ALGOKIT_CONFIG).write_text(config_data, encoding="utf-8")
    result = invoke("deploy", cwd=tmp_path)
    assert result.exit_code == 0
    verify(result.output.replace(python_executable, "<sys.executable>"))


def test_command_not_found_and_no_config(proc_mock: ProcMock) -> None:
    cmd = "gm"
    proc_mock.should_fail_on([cmd])
    result = invoke(["deploy", "--command", cmd])
    assert result.exit_code != 0
    verify(result.output)


def test_command_not_executable(proc_mock: ProcMock) -> None:
    cmd = "gm"
    proc_mock.should_deny_on([cmd])
    result = invoke(["deploy", "--command", cmd])
    assert result.exit_code != 0
    verify(result.output)


def test_command_bad_exit_code(proc_mock: ProcMock) -> None:
    cmd = "gm"
    proc_mock.should_bad_exit_on([cmd], output=["it is not morning"])
    result = invoke(["deploy", "--command", cmd])
    assert result.exit_code != 0
    verify(result.output)


def test_algokit_env_name_missing(tmp_path_factory: TempPathFactory) -> None:
    config_with_override = """
[deploy.localnet]
command = "command_a"
    """.strip()
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_override, encoding="utf-8")
    (cwd / ".env").touch()

    result = invoke(["deploy", "localnet"], cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_algokit_env_and_name_correct_set(
    tmp_path_factory: TempPathFactory, proc_mock: ProcMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_config = """
ENV_A=GENERIC_ENV_A
ENV_B=GENERIC_ENV_B
ENV_C=GENERIC_ENV_C
    """.strip()

    env_name_config = """
ENV_A=LOCALNET_ENV_A
ENV_B=LOCALNET_ENV_B
    """.strip()

    monkeypatch.setenv("ENV_A", "ENVIRON_ENV_A")

    config_with_deploy_name = """
[deploy]
command = "command_a"

[deploy.localnet]
command = "command_b"
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_deploy_name, encoding="utf-8")
    (cwd / ".env").write_text(env_config, encoding="utf-8")
    (cwd / ".env.localnet").write_text(env_name_config, encoding="utf-8")

    proc_mock.set_output(["command_b"], ["picked localnet"])

    result = invoke(["deploy", "localnet"], cwd=cwd)

    assert proc_mock.called[0].env
    passed_env_vars = proc_mock.called[0].env

    assert passed_env_vars["ENV_A"] == "ENVIRON_ENV_A"  # os.environ is highest loading priority
    assert passed_env_vars["ENV_B"] == "LOCALNET_ENV_B"  # then .env.{name}
    assert passed_env_vars["ENV_C"] == "GENERIC_ENV_C"  # lastly .env

    verify(result.output)


def test_algokit_deploy_only_base_deploy_config(tmp_path_factory: TempPathFactory, proc_mock: ProcMock) -> None:
    config_with_only_base_deploy = """
[deploy]
command = "command_a"
    """.strip()

    env_config = """
ENV_A=GENERIC_ENV_A
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_only_base_deploy, encoding="utf-8")
    (cwd / ".env").write_text(env_config, encoding="utf-8")

    proc_mock.set_output(["command_a"], ["picked base deploy command"])

    result = invoke(["deploy"], cwd=cwd)

    assert result.exit_code == 0
    assert proc_mock.called[0].env
    passed_env_vars = proc_mock.called[0].env

    assert passed_env_vars["ENV_A"] == "GENERIC_ENV_A"

    verify(result.output.replace(sys.executable, "<sys.executable>"))


def test_ci_flag_interactivity_mode_via_env(
    tmp_path_factory: TempPathFactory, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, proc_mock: ProcMock
) -> None:
    monkeypatch.setenv("CI", "true")
    cwd = tmp_path_factory.mktemp("cwd")

    mock_prompt = mocker.patch("click.prompt")

    config_with_only_base_deploy = """
[deploy]
command = "command_a"
environment_secrets = [
    "DEPLOYER_MNEMONIC"
]
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_only_base_deploy, encoding="utf-8")
    (cwd / ".env").touch()

    proc_mock.set_output(["command_a"], ["picked base deploy command"])

    result = invoke(["deploy"], cwd=cwd)

    mock_prompt.assert_not_called()
    assert result.exit_code != 0

    verify(result.output)


def test_ci_flag_interactivity_mode_via_cli(
    tmp_path_factory: TempPathFactory, mocker: MockerFixture, proc_mock: ProcMock
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mock_prompt = mocker.patch("click.prompt")

    config_with_only_base_deploy = """
[deploy]
command = "command_a"
environment_secrets = [
    "DEPLOYER_MNEMONIC"
]
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_only_base_deploy, encoding="utf-8")
    (cwd / ".env").touch()

    proc_mock.set_output(["command_a"], ["picked base deploy command"])

    result = invoke(["deploy", "--ci"], cwd=cwd)

    mock_prompt.assert_not_called()
    assert result.exit_code != 0

    verify(result.output)


# environment_secrets set
def test_secrets_prompting_via_stdin(
    tmp_path_factory: TempPathFactory, mocker: MockerFixture, proc_mock: ProcMock
) -> None:
    # mock click.prompt
    cwd = tmp_path_factory.mktemp("cwd")

    mock_prompt = mocker.patch("click.prompt", return_value="secret_value")
    config_with_only_base_deploy = """
[deploy]
command = "command_a"
environment_secrets = [
    "DEPLOYER_MNEMONIC"
]
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_only_base_deploy, encoding="utf-8")
    (cwd / ".env").touch()
    proc_mock.set_output(["command_a"], ["picked base deploy command"])

    result = invoke(["deploy"], cwd=cwd)
    mock_prompt.assert_called_once()  # ensure called
    assert result.exit_code == 0  # ensure success

    # assert that entered value is passed to proc run
    assert proc_mock.called[0].env
    called_env = proc_mock.called[0].env
    assert "DEPLOYER_MNEMONIC" in called_env
    assert called_env["DEPLOYER_MNEMONIC"] == "secret_value"

    verify(result.output)


def test_deploy_custom_project_dir(
    tmp_path_factory: TempPathFactory,
    proc_mock: ProcMock,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    custom_folder = cwd / "custom_folder"

    custom_folder.mkdir()
    (custom_folder / ALGOKIT_CONFIG).write_text(
        """
[deploy]
command = "command_a"
    """.strip(),
        encoding="utf-8",
    )
    (custom_folder / ".env.testnet").touch()
    proc_mock.set_output(["command_a"], ["picked base deploy command"])

    input_answers = ["N"]

    # Below is needed for escpaing the backslash in the path on Windows
    # Works on Linux as well since \\ doesnt exist in the path in such cases
    path = str(custom_folder.absolute()).replace("\\", r"\\")
    result = invoke(f"deploy testnet --path={path}", cwd=cwd, input="\n".join(input_answers))

    assert result.exit_code == 0
    verify(result.output)
