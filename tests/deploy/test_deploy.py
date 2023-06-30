import os

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.cli.deploy import extract_mnemonics
from algokit.core.constants import (
    ALGOKIT_CONFIG,
    ALGORAND_NETWORKS,
    BETANET,
    DEPLOYER_KEY,
    DISPENSER_KEY,
    LOCALNET,
    MAINNET,
    TESTNET,
)
from approvaltests.namer import NamerFactory

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke

DUMMY_NETWORK_CONF = """
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
ALGOD_SERVER=http://localhost
ALGOD_PORT=4001
INDEXER_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
INDEXER_SERVER=http://localhost
INDEXER_PORT=8980
"""
CUSTOMNET = "customnet"


# Unit tests for extract_mnemonics function
def test_extract_mnemonics() -> None:
    deployer_mnemonic, dispenser_mnemonic = extract_mnemonics(True, LOCALNET)  # noqa: FBT003
    assert not deployer_mnemonic
    assert not dispenser_mnemonic

    # Set environment variables for the test
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"
    os.environ[DISPENSER_KEY] = "test_dispenser_mnemonic"

    # Test extraction with skip_mnemonics_prompts=True
    deployer_mnemonic, dispenser_mnemonic = extract_mnemonics(True, LOCALNET)  # noqa: FBT003
    assert deployer_mnemonic == "test_deployer_mnemonic"
    assert dispenser_mnemonic == "test_dispenser_mnemonic"

    # Test extraction with skip_mnemonics_prompts=False and network != LOCALNET
    deployer_mnemonic, dispenser_mnemonic = extract_mnemonics(False, TESTNET)  # noqa: FBT003
    assert deployer_mnemonic == "test_deployer_mnemonic"
    assert dispenser_mnemonic == "test_dispenser_mnemonic"

    # Clean up environment variables
    del os.environ[DEPLOYER_KEY]
    del os.environ[DISPENSER_KEY]


# Approvals tests for deploy command
@pytest.mark.parametrize("network", ["", LOCALNET, TESTNET, MAINNET, BETANET, CUSTOMNET])
def test_deploy_no_algokit_toml(network: str, tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(
        result.output,
        options=NamerFactory.with_parameters(network),
    )


@pytest.mark.parametrize("network", [BETANET, LOCALNET, TESTNET, MAINNET])
def test_deploy_default_networks_no_env(network: str, tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    if network != LOCALNET:
        os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"

    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")

    input_answers = ["N" if network != LOCALNET else ""]

    if network == MAINNET:
        input_answers.append("Y")

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    assert result.exit_code == 0 if network == LOCALNET else 1
    verify(result.output, options=NamerFactory.with_parameters(network))


@pytest.mark.parametrize("has_env", [True, False])
def test_deploy_custom_network_env(has_env: bool, tmp_path_factory: TempPathFactory) -> None:  # noqa: FBT001
    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"
    network = CUSTOMNET

    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")

    if has_env:
        (cwd / f".env.{network}").write_text(DUMMY_NETWORK_CONF)

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="N",
    )

    assert result.exit_code == 0 if network == LOCALNET else 1
    verify(result.output, options=NamerFactory.with_parameters(has_env))


@pytest.mark.parametrize("env_network", [TESTNET, MAINNET])
def test_deploy_custom_network_env_genesis_call(env_network: str, tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"
    network = CUSTOMNET

    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")
    (cwd / f".env.{network}").write_text(
        f"""
    ALGOD_SERVER={ALGORAND_NETWORKS[env_network]['ALGOD_SERVER']}
    INDEXER_SERVER={ALGORAND_NETWORKS[env_network]['INDEXER_SERVER']}
    """
    )

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="N" if env_network == TESTNET else "N\nY",
    )

    assert result.exit_code == 0 if env_network == TESTNET else 1
    verify(result.output, options=NamerFactory.with_parameters(env_network))


def test_deploy_is_production_environment(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    network = MAINNET
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"

    # Setup algokit configuration file
    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")

    # Running with --prod flag
    result = invoke(
        f"deploy {network} --prod",
        cwd=cwd,
        input="N",
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.parametrize("network", [BETANET, LOCALNET, TESTNET, MAINNET, CUSTOMNET])
def test_deploy_custom_deploy_command(network: str, tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"

    custom_command = 'python -c print("HelloWorld")'
    if network == CUSTOMNET:
        (cwd / f".env.{network}").write_text(DUMMY_NETWORK_CONF)

    input_answers = ["N" if network != LOCALNET else ""]

    if network == MAINNET:
        input_answers.append("Y")

    # Running with --custom-deploy-command flag
    result = invoke(
        f"deploy {network} --custom-deploy-command '{custom_command}'",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    # Check if the custom deploy command is used
    assert result.exit_code == 0
    verify(result.output, options=NamerFactory.with_parameters(network))


def test_deploy_skip_mnemonics_prompts(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    network = TESTNET
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"

    # Setup algokit configuration file
    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")

    # Running with --ci flag to skip mnemonics prompts
    result = invoke(
        f"deploy {network} --ci",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)
