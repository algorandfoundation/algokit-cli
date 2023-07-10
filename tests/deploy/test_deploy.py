import os
import typing as t

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.cli.explore import NETWORKS
from algokit.core.conf import ALGOKIT_CONFIG
from approvaltests.namer import NamerFactory
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke

CUSTOMNET = "customnet"
LOCALNET_ALIASES = ("devnet", "sandnet", "dockernet")
LOCALNET = "localnet"
MAINNET = "mainnet"
BETANET = "betanet"
TESTNET = "testnet"

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
            "algokit.cli.deploy._is_localnet",
            return_value=key not in [*LOCALNET_ALIASES, LOCALNET],
        )

    return patch


# TODO: this should be tested through testing the deploy command,
#       not unit testing this short function
# # Your test can then simply use this fixture
# @mock.patch.dict("os.environ", {DEPLOYER_KEY: "", DISPENSER_KEY: ""})
# def test_extract_mnemonics_unset() -> None:
#     # Check when environment variables are not set
#     with pytest.raises(ClickException, match=f"missing {DEPLOYER_KEY}"):
#
#
# @mock.patch.dict("os.environ", {DEPLOYER_KEY: VALID_MNEMONIC1, DISPENSER_KEY: VALID_MNEMONIC2})
# def test_extract_mnemonics_set() -> None:
#
#     # Assert that the environment variables are not changed
#
#
# @mock.patch.dict("os.environ", {DEPLOYER_KEY: "abc", DISPENSER_KEY: VALID_MNEMONIC1})
# def test_extract_mnemonics_invalid_deployer() -> None:
#     with pytest.raises(ClickException, match=f"Invalid mnemonic for {DEPLOYER_KEY}"):
#
#
# @mock.patch.dict("os.environ", {DEPLOYER_KEY: VALID_MNEMONIC1, DISPENSER_KEY: "abc"})
# def test_extract_mnemonics_invalid_dispenser() -> None:
#     with pytest.raises(ClickException, match=f"Invalid mnemonic for {DISPENSER_KEY}"):
#


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


def _deploy_command(name: str) -> str:
    return f"""
[deploy.{name}]
command = "python -c 'print(\\"HelloWorld\\")'"
"""


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

    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(network))

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    assert result.exit_code == 0
    verify(result.output, options=NamerFactory.with_parameters(network))


def test_deploy_custom_env_no_file(tmp_path_factory: TempPathFactory, mock_network_genesis: MockNetworkGenesis) -> None:
    name = "staging"
    mock_network_genesis(TESTNET)

    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = VALID_MNEMONIC1

    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(name))

    input_answers = ["N"]

    result = invoke(f"deploy {name}", cwd=cwd, input="\n".join(input_answers))

    assert result.exit_code == 1
    verify(result.output)


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
    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(network))
    (custom_folder / (".env" if generic_env else f".env.{network}")).write_text(
        f"""
    ALGOD_SERVER={NETWORKS[network]['algod_url']}
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

    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(network))

    if has_env:
        (cwd / f".env.{network}").write_text(
            # Use a dummy network that doesn't require running localnet but is queryable
            f"""
             ALGOD_SERVER={NETWORKS[TESTNET]['algod_url']}
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
    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(network))

    # Running with --prod flag
    result = invoke(
        f"deploy {network} --no-mainnet-prompt",
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

    if network not in NETWORKS:
        (cwd / f".env.{network}").write_text(f"ALGOD_SERVER={NETWORKS[TESTNET]['algod_url']}")

    input_answers: list[str] = []
    if network != LOCALNET:
        if network == MAINNET:
            input_answers.append("Y")
        input_answers.append("N")

    # Running with --command flag
    result = invoke(
        f"deploy {network} --command 'python -c print(123)'",
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
    (cwd / ALGOKIT_CONFIG).write_text(_deploy_command(network))

    # Running with --ci flag to skip mnemonics prompts
    result = invoke(
        f"deploy {network} --ci",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)
