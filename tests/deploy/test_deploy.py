import os
import typing as t
from unittest import mock

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.cli.deploy import DEPLOYER_KEY, DISPENSER_KEY, ensure_mnemonics
from algokit.core.conf import ALGOKIT_CONFIG
from algokit.core.deploy import ALGORAND_NETWORKS, BETANET, LOCALNET, LOCALNET_ALIASES, MAINNET, TESTNET
from approvaltests.namer import NamerFactory
from click import ClickException
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke

CUSTOMNET = "customnet"


VALID_MNEMONIC1 = (
    "until random potato live stove poem toddler deliver give traffic vapor genuine "
    "supply wonder few gap penalty ask cluster high throw own milk ability issue"
)
VALID_MNEMONIC2 = (
    "cruise sustain matrix bulb bind aisle fox copper antenna arctic brief video cactus "
    "high rough lawn secret dignity inmate remember early pudding collect about trick"
)


MockNetworkGenesis = t.Callable[[str], None]


@pytest.fixture()
def mock_network_genesis(mocker: MockerFixture) -> MockNetworkGenesis:
    def patch(key: str) -> None:
        mocker.patch(
            "algokit.cli.deploy._get_network_name_from_environment",
            return_value=key if key != LOCALNET else LOCALNET_ALIASES[0],
        )

    return patch


# Your test can then simply use this fixture
@mock.patch.dict("os.environ", {DEPLOYER_KEY: "", DISPENSER_KEY: ""})
def test_extract_mnemonics_unset() -> None:
    # Check when environment variables are not set
    with pytest.raises(ClickException, match=f"missing {DEPLOYER_KEY}"):
        ensure_mnemonics(skip_mnemonics_prompts=True)


@mock.patch.dict("os.environ", {DEPLOYER_KEY: VALID_MNEMONIC1, DISPENSER_KEY: VALID_MNEMONIC2})
def test_extract_mnemonics_set() -> None:
    ensure_mnemonics(skip_mnemonics_prompts=True)

    # Assert that the environment variables are not changed
    assert os.environ[DEPLOYER_KEY] == VALID_MNEMONIC1
    assert os.environ[DISPENSER_KEY] == VALID_MNEMONIC2


@mock.patch.dict("os.environ", {DEPLOYER_KEY: "abc", DISPENSER_KEY: VALID_MNEMONIC1})
def test_extract_mnemonics_invalid_deployer() -> None:
    with pytest.raises(ClickException, match=f"Invalid mnemonic for {DEPLOYER_KEY}"):
        ensure_mnemonics(skip_mnemonics_prompts=True)


@mock.patch.dict("os.environ", {DEPLOYER_KEY: VALID_MNEMONIC1, DISPENSER_KEY: "abc"})
def test_extract_mnemonics_invalid_dispenser() -> None:
    with pytest.raises(ClickException, match=f"Invalid mnemonic for {DISPENSER_KEY}"):
        ensure_mnemonics(skip_mnemonics_prompts=True)


# Approvals tests for deploy command
@pytest.mark.parametrize("network", ["", LOCALNET, TESTNET, MAINNET, BETANET, CUSTOMNET])
def test_deploy_no_algokit_toml(
    network: str, tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis
) -> None:
    mock_network_genesis(network)

    if network != LOCALNET:
        os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1

    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="N",
    )

    assert result.exit_code == 1
    verify(
        result.output,
        options=NamerFactory.with_parameters(network),
    )


@pytest.mark.parametrize("network", [BETANET, LOCALNET, TESTNET, MAINNET])
def test_deploy_default_networks_no_env(
    network: str, tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis
) -> None:
    mock_network_genesis(network)

    cwd = tmp_path_factory.mktemp("cwd")
    input_answers: list[str] = []
    if network != LOCALNET:
        os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1
        if network == MAINNET:
            input_answers.append("Y")
        input_answers.append("N")

    (cwd / ALGOKIT_CONFIG).write_text(f'[deploy.{network}]\ncommand = "python -c print("HelloWorld")"\n')

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    assert result.exit_code == 0 if network == LOCALNET else 1
    verify(result.output, options=NamerFactory.with_parameters(network))


@pytest.mark.parametrize("network", [BETANET, CUSTOMNET])
def test_deploy_generic_env(
    network: str, tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis
) -> None:
    mock_network_genesis(network)

    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1

    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")
    network_key = network if network == BETANET else MAINNET
    (cwd / ".env").write_text(
        f"""
    ALGOD_SERVER={ALGORAND_NETWORKS[network_key]['ALGOD_SERVER']}
    """
    )

    input_answers = ["N"]

    if network_key == MAINNET:
        input_answers.append("Y")

    result = invoke(f"deploy {network}", cwd=cwd, input="\n".join(input_answers))

    assert result.exit_code == 0 if network == LOCALNET else 1
    verify(result.output, options=NamerFactory.with_parameters(network))


@pytest.mark.parametrize("generic_env", [True, False])
def test_deploy_custom_project_dir(
    generic_env: bool, tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis  # noqa: FBT001
) -> None:
    network = TESTNET
    mock_network_genesis(network)

    cwd = tmp_path_factory.mktemp("cwd")
    custom_folder = cwd / "custom_folder"
    os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1

    custom_folder.mkdir()
    (custom_folder / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")
    (custom_folder / (".env" if generic_env else f".env.{network}")).write_text(
        f"""
    ALGOD_SERVER={ALGORAND_NETWORKS[network]['ALGOD_SERVER']}
    """
    )

    input_answers = ["N"]

    # Below is needed for escpaing the backslash in the path on Windows
    # Works on Linux as well since \\ doesnt exist in the path in such cases
    path = str(custom_folder.absolute()).replace("\\", r"\\")
    result = invoke(f"deploy {network} --path={path}", cwd=cwd, input="\n".join(input_answers))

    assert result.exit_code == 0 if network == LOCALNET else 1
    verify(result.output, options=NamerFactory.with_parameters(generic_env))


@pytest.mark.parametrize("has_env", [True, False])
def test_deploy_custom_network_env(
    has_env: bool, tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis  # noqa: FBT001
) -> None:
    network = CUSTOMNET
    mock_network_genesis(network)

    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1

    (cwd / ALGOKIT_CONFIG).write_text(
        f"""
[deploy.{network}]
command = "python -c print('HelloWorld')"
"""
    )

    if has_env:
        (cwd / f".env.{network}").write_text(
            # Use a dummy network that doesn't require running localnet but is queryable
            f"""
             ALGOD_SERVER={ALGORAND_NETWORKS[TESTNET]['ALGOD_SERVER']}
            """
        )

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="N",
    )

    assert result.exit_code == 0 if network == LOCALNET else 1
    verify(result.output, options=NamerFactory.with_parameters(has_env))


def test_deploy_is_production_environment(
    tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis
) -> None:
    network = MAINNET
    mock_network_genesis(network)

    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1

    # Setup algokit configuration file
    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")

    # Running with --prod flag
    result = invoke(
        f"deploy {network} --enable-prod-deploys",
        cwd=cwd,
        input="N",
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.parametrize("network", [BETANET, LOCALNET, TESTNET, MAINNET, CUSTOMNET])
def test_deploy_custom_deploy_command(
    network: str, tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis
) -> None:
    mock_network_genesis(network)

    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1

    custom_command = 'python -c print("HelloWorld")'
    if network == CUSTOMNET:
        (cwd / f".env.{network}").write_text(
            f"""
                ALGOD_SERVER={ALGORAND_NETWORKS[TESTNET]['ALGOD_SERVER']}
            """
        )

    input_answers: list[str] = []
    if network != LOCALNET:
        if network == MAINNET:
            input_answers.append("Y")
        input_answers.append("N")

    # Running with --command flag
    result = invoke(
        f"deploy {network} --command '{custom_command}'",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    # Check if the custom deploy command is used
    assert result.exit_code == 0
    verify(result.output, options=NamerFactory.with_parameters(network))


def test_deploy_skip_mnemonics_prompts(
    tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis
) -> None:
    network = TESTNET
    mock_network_genesis(network)

    cwd = tmp_path_factory.mktemp("cwd")

    os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1

    # Setup algokit configuration file
    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")

    # Running with --ci flag to skip mnemonics prompts
    result = invoke(
        f"deploy {network} --ci",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)
