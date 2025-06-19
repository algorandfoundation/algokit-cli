import json
import sys
from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from algosdk.account import generate_account
from algosdk.mnemonic import from_private_key
from approvaltests.namer import NamerFactory
from pytest_mock import MockerFixture

from algokit.cli.common.utils import sanitize_extra_args
from algokit.core.conf import ALGOKIT_CONFIG
from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock
from tests.utils.which_mock import WhichMock

PYTHON_EXECUTABLE = sys.executable
# need to use an escaped python executable path in config files for windows
PYTHON_EXECUTABLE_ESCAPED = PYTHON_EXECUTABLE.replace("\\", "\\\\")
# note: spaces around the string inside print are important,
# we need to test the usage of shlex.split vs str.split, to handle
# splitting inside quotes properly
TEST_PYTHON_COMMAND = "print(' test_command_invocation ')"


@pytest.fixture(autouse=True)
def which_mock(mocker: MockerFixture) -> WhichMock:
    which_mock = WhichMock()
    mocker.patch("algokit.core.utils.shutil.which").side_effect = which_mock.which
    return which_mock


def test_algokit_config_empty_array(tmp_path_factory: TempPathFactory) -> None:
    empty_array_config = """
[project.deploy]
command = []
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(empty_array_config, encoding="utf-8")
    (cwd / ".env").touch()
    result = invoke(["project", "deploy"], cwd=cwd)

    assert result.exit_code != 0
    verify(result.output)


def test_algokit_config_invalid_syntax(tmp_path_factory: TempPathFactory) -> None:
    invalid_config = """
{"dummy": "json"}
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(invalid_config, encoding="utf-8")
    (cwd / ".env").touch()
    result = invoke(["project", "deploy"], cwd=cwd)

    assert result.exit_code != 0
    verify(result.output)


def test_algokit_config_name_overrides(
    tmp_path_factory: TempPathFactory, proc_mock: ProcMock, which_mock: WhichMock
) -> None:
    config_with_override = """
[project.deploy]
command = "command_a"

[project.deploy.localnet]
command = "command_b"

[project.deploy.testnet]
command = "command_c"
    """.strip()
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_override, encoding="utf-8")
    (cwd / ".env").touch()
    (cwd / ".env.localnet").touch()
    (cwd / ".env.testnet").touch()

    resolved_cmd = which_mock.add("command_c")
    proc_mock.set_output([resolved_cmd], ["picked testnet"])

    result = invoke(["project", "deploy", "testnet"], cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)


def test_algokit_config_name_no_base(
    tmp_path_factory: TempPathFactory, proc_mock: ProcMock, which_mock: WhichMock
) -> None:
    config_with_override = """
[project.deploy.localnet]
command = "command_a"

[project.deploy.testnet]
command = "command_b"
    """.strip()
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_override, encoding="utf-8")
    (cwd / ".env.localnet").touch()
    (cwd / ".env.testnet").touch()

    cmd = which_mock.add("command_a")
    proc_mock.set_output([cmd], ["picked localnet"])

    result = invoke(["project", "deploy", "localnet"], cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)


def test_command_invocation_and_command_splitting(tmp_path: Path) -> None:
    config_data = """
[project.deploy]
command = ["not", "used"]
    """.strip()
    (tmp_path / ALGOKIT_CONFIG).write_text(config_data, encoding="utf-8")
    result = invoke(
        [
            "project",
            "deploy",
            "--command",
            f'{PYTHON_EXECUTABLE} -c "{TEST_PYTHON_COMMAND}"',
        ],
        cwd=tmp_path,
    )
    assert result.exit_code == 0
    verify(result.output.replace(PYTHON_EXECUTABLE, "<sys.executable>"))


def test_command_splitting_from_config(tmp_path: Path) -> None:
    config_data = rf"""
[project.deploy]
command = "{PYTHON_EXECUTABLE_ESCAPED} -c \"{TEST_PYTHON_COMMAND}\""
    """.strip()
    (tmp_path / ALGOKIT_CONFIG).write_text(config_data, encoding="utf-8")
    result = invoke(["project", "deploy"], cwd=tmp_path)
    assert result.exit_code == 0
    verify(result.output.replace(PYTHON_EXECUTABLE, "<sys.executable>"))


def test_command_without_splitting_from_config(tmp_path: Path) -> None:
    config_data = rf"""
[project.deploy]
command = ["{PYTHON_EXECUTABLE_ESCAPED}", "-c", "{TEST_PYTHON_COMMAND}"]
    """.strip()
    (tmp_path / ALGOKIT_CONFIG).write_text(config_data, encoding="utf-8")
    result = invoke(["project", "deploy"], cwd=tmp_path)
    assert result.exit_code == 0
    verify(result.output.replace(PYTHON_EXECUTABLE, "<sys.executable>"))


@pytest.mark.usefixtures("proc_mock")
def test_command_not_found_and_no_config(tmp_path: Path) -> None:
    cmd = "gm"
    result = invoke(["project", "deploy", "--command", cmd], cwd=tmp_path)
    assert result.exit_code != 0
    verify(result.output)


def test_command_not_executable(proc_mock: ProcMock, tmp_path: Path, which_mock: WhichMock) -> None:
    cmd = "gm"
    cmd_resolved = which_mock.add(cmd)
    proc_mock.should_deny_on([cmd_resolved])
    result = invoke(["project", "deploy", "--command", cmd], cwd=tmp_path)
    assert result.exit_code != 0
    verify(result.output)


def test_command_bad_exit_code(proc_mock: ProcMock, tmp_path: Path, which_mock: WhichMock) -> None:
    cmd = "gm"
    cmd_resolved = which_mock.add(cmd)
    proc_mock.should_bad_exit_on([cmd_resolved], output=["it is not morning"])
    result = invoke(["project", "deploy", "--command", cmd], cwd=tmp_path)
    assert result.exit_code != 0
    verify(result.output)


def test_algokit_env_name_missing(tmp_path_factory: TempPathFactory, which_mock: WhichMock) -> None:
    config_with_override = """
[project.deploy.customnet]
command = "command_a"
    """.strip()
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_override, encoding="utf-8")
    (cwd / ".env").touch()

    which_mock.add("command_a")
    result = invoke(["project", "deploy", "customnet"], cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_algokit_env_and_name_correct_set(
    tmp_path_factory: TempPathFactory, proc_mock: ProcMock, monkeypatch: pytest.MonkeyPatch, which_mock: WhichMock
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
[project.deploy]
command = "command_a"

[project.deploy.localnet]
command = "command_b"
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_deploy_name, encoding="utf-8")
    (cwd / ".env").write_text(env_config, encoding="utf-8")
    (cwd / ".env.localnet").write_text(env_name_config, encoding="utf-8")

    cmd_resolved = which_mock.add("command_b")
    proc_mock.set_output([cmd_resolved], ["picked localnet"])

    result = invoke(["project", "deploy", "localnet"], cwd=cwd)

    assert proc_mock.called[0].env
    passed_env_vars = proc_mock.called[0].env

    assert passed_env_vars["ENV_A"] == "ENVIRON_ENV_A"  # os.environ is highest loading priority
    assert passed_env_vars["ENV_B"] == "LOCALNET_ENV_B"  # then .env.{name}
    assert passed_env_vars["ENV_C"] == "GENERIC_ENV_C"  # lastly .env

    verify(result.output)


def test_algokit_deploy_only_base_deploy_config(
    tmp_path_factory: TempPathFactory, proc_mock: ProcMock, which_mock: WhichMock
) -> None:
    config_with_only_base_deploy = """
[project.deploy]
command = "command_a"
    """.strip()

    env_config = """
ENV_A=GENERIC_ENV_A
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_only_base_deploy, encoding="utf-8")
    (cwd / ".env").write_text(env_config, encoding="utf-8")

    cmd_resolved = which_mock.add("command_a")
    proc_mock.set_output([cmd_resolved], ["picked base deploy command"])

    result = invoke(["project", "deploy"], cwd=cwd)

    assert result.exit_code == 0
    assert proc_mock.called[0].env
    passed_env_vars = proc_mock.called[0].env

    assert passed_env_vars["ENV_A"] == "GENERIC_ENV_A"

    verify(result.output)


def test_ci_flag_interactivity_mode_via_env(
    tmp_path_factory: TempPathFactory,
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    proc_mock: ProcMock,
    which_mock: WhichMock,
) -> None:
    monkeypatch.setenv("CI", "true")

    mock_prompt = mocker.patch("click.prompt")

    config_with_only_base_deploy = """
[project.deploy]
command = "command_a"
environment_secrets = [
    "DEPLOYER_MNEMONIC"
]
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_only_base_deploy, encoding="utf-8")
    (cwd / ".env").touch()

    cmd_resolved = which_mock.add("command_a")
    proc_mock.set_output([cmd_resolved], ["picked base deploy command"])

    result = invoke(["project", "deploy"], cwd=cwd)

    mock_prompt.assert_not_called()
    assert result.exit_code != 0

    verify(result.output)


def test_ci_flag_interactivity_mode_via_cli(
    tmp_path_factory: TempPathFactory,
    mocker: MockerFixture,
    proc_mock: ProcMock,
    which_mock: WhichMock,
) -> None:
    mock_prompt = mocker.patch("click.prompt")

    config_with_only_base_deploy = """
[project.deploy]
command = "command_a"
environment_secrets = [
    "DEPLOYER_MNEMONIC"
]
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_only_base_deploy, encoding="utf-8")
    (cwd / ".env").touch()

    cmd_resolved = which_mock.add("command_a")
    proc_mock.set_output([cmd_resolved], ["picked base deploy command"])

    result = invoke(["project", "deploy", "--ci"], cwd=cwd)

    mock_prompt.assert_not_called()
    assert result.exit_code != 0

    verify(result.output)


# environment_secrets set
def test_secrets_prompting_via_stdin(
    tmp_path_factory: TempPathFactory,
    mocker: MockerFixture,
    proc_mock: ProcMock,
    monkeypatch: pytest.MonkeyPatch,
    which_mock: WhichMock,
) -> None:
    # ensure Github Actions CI env var is not overriding behavior
    monkeypatch.delenv("CI", raising=False)

    # mock click.prompt
    mock_prompt = mocker.patch("click.prompt", return_value="secret_value")
    config_with_only_base_deploy = """
[project.deploy]
command = "command_a"
environment_secrets = [
    "DEPLOYER_MNEMONIC"
]
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_only_base_deploy, encoding="utf-8")
    (cwd / ".env").touch()
    cmd_resolved = which_mock.add("command_a")
    proc_mock.set_output([cmd_resolved], ["picked base deploy command"])

    result = invoke(["project", "deploy"], cwd=cwd)
    mock_prompt.assert_called_once()  # ensure called
    assert result.exit_code == 0  # ensure success

    # assert that entered value is passed to proc run
    assert proc_mock.called[0].env
    called_env = proc_mock.called[0].env
    assert "DEPLOYER_MNEMONIC" in called_env
    assert called_env["DEPLOYER_MNEMONIC"] == "secret_value"

    verify(result.output)


def test_deploy_custom_project_dir(
    tmp_path_factory: TempPathFactory, proc_mock: ProcMock, which_mock: WhichMock
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    custom_folder = cwd / "custom_folder"

    custom_folder.mkdir()
    (custom_folder / ALGOKIT_CONFIG).write_text(
        """
[project.deploy]
command = "command_a"
    """.strip(),
        encoding="utf-8",
    )
    (custom_folder / ".env.testnet").touch()
    cmd_resolved = which_mock.add("command_a")
    proc_mock.set_output([cmd_resolved], ["picked base deploy command"])

    input_answers = ["N"]

    # Below is needed for escaping the backslash in the path on Windows
    # Works on Linux as well since \\ doesn't exist in the path in such cases
    path = str(custom_folder.absolute()).replace("\\", r"\\")
    result = invoke(f"project deploy testnet --path={path}", cwd=cwd, input="\n".join(input_answers))

    assert result.exit_code == 0
    verify(result.output)


def test_deploy_shutil_command_not_found(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / ALGOKIT_CONFIG).write_text(
        """
[project.deploy]
command = "command_a"
    """.strip(),
        encoding="utf-8",
    )
    (cwd / ".env").touch()

    result = invoke(["project", "deploy"], cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.parametrize(
    ("alias", "env_var_name"),
    [
        ("deployer", "DEPLOYER_MNEMONIC"),
        ("dispenser", "DISPENSER_MNEMONIC"),
    ],
)
def test_deploy_dispenser_alias(
    alias: str,
    env_var_name: str,
    tmp_path_factory: TempPathFactory,
    proc_mock: ProcMock,
    monkeypatch: pytest.MonkeyPatch,
    mock_keyring: dict[str, str],
    which_mock: WhichMock,
) -> None:
    env_config = f"""
{env_var_name}=GENERIC_ENV_A
    """.strip()

    monkeypatch.setenv(env_var_name, "GENERIC_ENV_A")

    config_with_deploy_name = f"""
[project.deploy]
command = "command_a"
environment_secrets = [
    "{env_var_name}"
]
    """.strip()

    dummy_account_pk, dummy_account_addr = generate_account()  # type: ignore[no-untyped-call]
    mock_keyring[alias] = json.dumps({"alias": alias, "address": dummy_account_addr, "private_key": dummy_account_pk})
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias])

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_deploy_name, encoding="utf-8")
    (cwd / ".env").write_text(env_config, encoding="utf-8")
    which_mock.add("command_a")
    result = invoke(["project", "deploy", f"--{alias}", alias], cwd=cwd)

    assert proc_mock.called[0].env
    passed_env_vars = proc_mock.called[0].env

    assert passed_env_vars[env_var_name] == from_private_key(dummy_account_pk)  # type: ignore[no-untyped-call]

    verify(result.output, options=NamerFactory.with_parameters(alias))


def test_deploy_with_extra_args(tmp_path_factory: TempPathFactory, proc_mock: ProcMock, which_mock: WhichMock) -> None:
    config_with_deploy = """
[project.deploy]
command = "command_a"
    """.strip()

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(config_with_deploy, encoding="utf-8")
    (cwd / ".env").touch()

    cmd_resolved = which_mock.add("command_a")
    proc_mock.set_output([cmd_resolved], ["command executed"])

    extra_args = ["--arg1 value1 --arg2 value2"]
    result = invoke(["project", "deploy", "--", *extra_args], cwd=cwd)

    assert result.exit_code == 0
    assert proc_mock.called[0].command == [cmd_resolved, *sanitize_extra_args(extra_args)]
    verify(result.output)


def test_deploy_with_extra_args_and_custom_command(
    tmp_path_factory: TempPathFactory, proc_mock: ProcMock, which_mock: WhichMock
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env").touch()

    custom_command = "custom_command"
    cmd_resolved = which_mock.add(custom_command)
    proc_mock.set_output([cmd_resolved], ["custom command executed"])

    extra_args = ["--custom-arg1 custom-value1 --custom-arg2 custom-value2"]
    result = invoke(["project", "deploy", "localnet", "--command", custom_command, "--", *extra_args], cwd=cwd)

    assert result.exit_code == 0
    assert proc_mock.called[0].command == [cmd_resolved, *sanitize_extra_args(extra_args)]
    verify(result.output)
