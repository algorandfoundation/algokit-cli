import sys
from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.cli.explore import NETWORKS
from algokit.core.conf import ALGOKIT_CONFIG
from approvaltests.namer import NamerFactory

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock

CUSTOMNET = "customnet"
LOCALNET_ALIASES = ("devnet", "sandnet", "dockernet")
LOCALNET = "localnet"
MAINNET = "mainnet"
BETANET = "betanet"
TESTNET = "testnet"
DEPLOYER_KEY = "DEPLOYER_MNEMONIC"
DISPENSER_KEY = "DISPENSER_MNEMONIC"

VALID_MNEMONIC1 = (
    "until random potato live stove poem toddler deliver give traffic vapor genuine "
    "supply wonder few gap penalty ask cluster high throw own milk ability issue"
)
VALID_MNEMONIC2 = (
    "cruise sustain matrix bulb bind aisle fox copper antenna arctic brief video cactus "
    "high rough lawn secret dignity inmate remember early pudding collect about trick"
)


@pytest.fixture(autouse=True)
def _set_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DEPLOYER_KEY, VALID_MNEMONIC1)


def _deploy_command(*, environment: str, prefixed: bool, exclude_command: bool = False) -> str:
    command = 'command = "python -c \'print(\\"HelloWorld\\")\'"' if not exclude_command else ""

    if prefixed:
        return f"""
[deploy.{environment}]
{command}
environment_secrets = [
  "DEPLOYER_MNEMONIC"
]
"""
    return f"""
[deploy]
{command}
environment_secrets = [
  "DEPLOYER_MNEMONIC"
]
"""


def _dummy_env() -> str:
    return """
ALGOD_SERVER=https://testnet-api.algonode.cloud
"""


# DIMENSIONS:
# - algokit.toml
#   - missing
#   - invalid configs (e.g. empty array)
#   - {name} overrides
#   - {name} setting with no "base case"
# - .env and/or .env.{name}
# - os.environ
# - CI (interactivity) mode
# - path option


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


def test_command_not_found(proc_mock: ProcMock) -> None:
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


@pytest.mark.usefixtures("proc_mock")
def test_deploy_check_passed_env_vars(tmp_path_factory: TempPathFactory, proc_mock: ProcMock) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(environment=TESTNET, prefixed=True))
    (cwd / f".env.{TESTNET}").write_text(_dummy_env())

    # Running with --command flag
    result = invoke(
        f"deploy {TESTNET}",
        cwd=cwd,
    )

    # Check if the custom deploy command is used
    assert result.exit_code == 0
    assert len(proc_mock.called) == 1
    called_env = proc_mock.called[0].env
    assert isinstance(called_env, dict)
    assert DEPLOYER_KEY in called_env
    assert called_env[DEPLOYER_KEY] == str(VALID_MNEMONIC1)
    verify(result.output)


@pytest.mark.parametrize(
    ("environment"),
    [BETANET, LOCALNET, TESTNET, MAINNET, CUSTOMNET],
)
def test_deploy_various_networks_with_prefixed_env(*, environment: str, tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    input_answers: list[str] = []

    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(environment=environment, prefixed=True))
    (cwd / (f".env.{environment}")).write_text(_dummy_env())

    result = invoke(
        f"deploy {environment}",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    assert result.exit_code == 0
    verify(result.output, options=NamerFactory.with_parameters(environment))


@pytest.mark.parametrize(
    ("environment"),
    [BETANET, LOCALNET, TESTNET, MAINNET, CUSTOMNET],
)
def test_deploy_various_networks_with_generic_env(*, environment: str, tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    input_answers: list[str] = []

    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(environment=environment, prefixed=False))
    (cwd / (".env")).write_text(_dummy_env())

    result = invoke(
        "deploy",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    assert result.exit_code == 0
    verify(result.output, options=NamerFactory.with_parameters(environment))


@pytest.mark.parametrize("prefixed_env", [True, False])
def test_deploy_custom_env_no_file(
    *,
    prefixed_env: bool,
    tmp_path_factory: TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(environment=TESTNET, prefixed=prefixed_env))

    result = invoke(
        f"deploy {TESTNET if prefixed_env else ''}",
        cwd=cwd,
    )

    assert result.exit_code == (1 if prefixed_env else 0)
    verify(result.output, options=NamerFactory.with_parameters(prefixed_env))


def test_deploy_custom_project_dir(
    tmp_path_factory: TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    custom_folder = cwd / "custom_folder"

    custom_folder.mkdir()
    (custom_folder / ALGOKIT_CONFIG).write_text(_deploy_command(environment=TESTNET, prefixed=True))
    (custom_folder / f".env.{TESTNET}").write_text(_dummy_env())

    input_answers = ["N"]

    # Below is needed for escpaing the backslash in the path on Windows
    # Works on Linux as well since \\ doesnt exist in the path in such cases
    path = str(custom_folder.absolute()).replace("\\", r"\\")
    result = invoke(f"deploy {TESTNET} --path={path}", cwd=cwd, input="\n".join(input_answers))

    assert result.exit_code == 0
    verify(result.output)


def test_deploy_custom_deploy_command(
    tmp_path_factory: TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(environment=TESTNET, prefixed=True, exclude_command=True))
    (cwd / f".env.{TESTNET}").write_text(_dummy_env())

    # Running with --command flag
    result = invoke(
        f"deploy {TESTNET} --command 'python -c print(123)'",
        cwd=cwd,
    )

    # Check if the custom deploy command is used
    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.parametrize("use_ci", [True, False])
def test_deploy_mnemonic_prompts(
    *, use_ci: bool, tmp_path_factory: TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    network = TESTNET

    cwd = tmp_path_factory.mktemp("cwd")

    # remove ci flag from env (when running in github actions)
    monkeypatch.delenv("CI", raising=False)

    if not use_ci:
        monkeypatch.delenv(DEPLOYER_KEY, raising=False)

    # Setup algokit configuration file
    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(environment=TESTNET, prefixed=True))
    (cwd / f".env.{network}").write_text(f"ALGOD_SERVER={NETWORKS[TESTNET]['algod_url']}")

    # Running with --ci flag to skip mnemonics prompts
    result = invoke(
        f"deploy {network} {'--ci' if use_ci else ''}",
        cwd=cwd,
        input="Ctrl+C" if not use_ci else None,
    )

    assert result.exit_code == 0
    verify(
        result.output.replace("DEPLOYER_MNEMONIC: ", "DEPLOYER_MNEMONIC:"), options=NamerFactory.with_parameters(use_ci)
    )
