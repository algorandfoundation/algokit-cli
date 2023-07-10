from unittest import mock

import click
import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.cli.deploy import _ensure_environment_secrets
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


# Unit tests for mnemonics


def test_ensure_environment_secrets_unset() -> None:
    # Define a fake 'click.prompt' that raises an Exception to simulate user interrupt (Ctrl+C)
    def mock_prompt(
        text: str,  # noqa: ARG001
        hide_input: bool,  # noqa: FBT001, ARG001
    ) -> str:
        raise Exception("Simulated user interrupt")

    # Patch 'click.prompt' with our fake version
    with mock.patch("click.prompt", new=mock_prompt):
        config_env: dict[str, str] = {}
        environment_secrets: list[str] = [DEPLOYER_KEY, DISPENSER_KEY]
        with pytest.raises(click.ClickException, match=f"Error: missing {DEPLOYER_KEY} environment variable"):
            _ensure_environment_secrets(config_env, environment_secrets, skip_mnemonics_prompts=True)


def test_ensure_environment_secrets_set() -> None:
    config_env: dict[str, str] = {DEPLOYER_KEY: VALID_MNEMONIC1, DISPENSER_KEY: VALID_MNEMONIC2}
    environment_secrets: list[str] = [DEPLOYER_KEY, DISPENSER_KEY]
    _ensure_environment_secrets(config_env, environment_secrets, skip_mnemonics_prompts=True)
    assert config_env[DEPLOYER_KEY] == VALID_MNEMONIC1
    assert config_env[DISPENSER_KEY] == VALID_MNEMONIC2


def test_ensure_environment_secrets_prompt() -> None:
    # Define a fake 'click.prompt' that returns a fixed mnemonic
    def mock_prompt(
        text: str,  # noqa: ARG001
        hide_input: bool,  # noqa: FBT001, ARG001
    ) -> str:
        return VALID_MNEMONIC1

    # Patch 'click.prompt' with our fake version
    with mock.patch("click.prompt", new=mock_prompt):
        config_env: dict[str, str] = {}
        environment_secrets: list[str] = [DEPLOYER_KEY, DISPENSER_KEY]
        _ensure_environment_secrets(config_env, environment_secrets, skip_mnemonics_prompts=False)
        assert config_env[DEPLOYER_KEY] == VALID_MNEMONIC1
        assert config_env[DISPENSER_KEY] == VALID_MNEMONIC1


# Approvals tests for deploy command


def test_deploy_no_algokit_toml(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "deploy ",
        cwd=cwd,
        input="N",
    )

    assert result.exit_code == 1
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
    assert DEPLOYER_KEY in proc_mock.env
    assert proc_mock.env[DEPLOYER_KEY] == str(VALID_MNEMONIC1)
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
    monkeypatch.delenv("CI")

    if not use_ci:
        monkeypatch.delenv(DEPLOYER_KEY)

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
