import os

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.cli.deploy import DEPLOYER_KEY, DISPENSER_KEY, LOCALNET, extract_env_variables
from algokit.core.constants import ALGOKIT_CONFIG
from approvaltests.namer import NamerFactory

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


# Unit tests for extract_env_variables function
def test_extract_env_variables() -> None:
    # Set environment variables for the test
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"
    os.environ[DISPENSER_KEY] = "test_dispenser_mnemonic"

    # Test extraction with skip_mnemonics_prompts=True
    deployer_mnemonic, dispenser_mnemonic = extract_env_variables(True, LOCALNET)  # noqa: FBT003
    assert deployer_mnemonic == "test_deployer_mnemonic"
    assert dispenser_mnemonic == "test_dispenser_mnemonic"

    # Test extraction with skip_mnemonics_prompts=False and network != LOCALNET
    deployer_mnemonic, dispenser_mnemonic = extract_env_variables(False, "testnet")  # noqa: FBT003
    assert deployer_mnemonic == "test_deployer_mnemonic"
    assert dispenser_mnemonic == "test_dispenser_mnemonic"

    # Clean up environment variables
    del os.environ[DEPLOYER_KEY]
    del os.environ[DISPENSER_KEY]


# Approvals tests for deploy command
@pytest.mark.parametrize("network", ["", "localnet", "testnet", "mainnet", "betanet", "customnet"])
def test_deploy_command_no_algokit_toml(network: str, tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(
        result.output,
    )


@pytest.mark.parametrize("network", ["betanet", "localnet", "testnet", "mainnet"])
def test_deploy_command_default_networks_no_env(network: str, tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    if network != "localnet":
        os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"

    (cwd / ALGOKIT_CONFIG).write_text(f'[deploy.{network}]\ncommand = "echo HelloWorld"\n')

    input_answers = ["N" if network != "localnet" else ""]

    if network == "mainnet":
        input_answers.append("Y")

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    assert result.exit_code == 0 if network == "localnet" else 1
    verify(result.output, options=NamerFactory.with_parameters(network))


@pytest.mark.parametrize("has_env", [True, False])
def test_deploy_command_custom_network_no_env(has_env: bool, tmp_path_factory: TempPathFactory) -> None:  # noqa: FBT001
    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"
    network = "customnet"

    (cwd / ALGOKIT_CONFIG).write_text(f'[deploy.{network}]\ncommand = "echo HelloWorld"\n')

    if has_env:
        (cwd / f".env.{network}").write_text(
            """
            ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            ALGOD_SERVER=http://localhost
            ALGOD_PORT=4001
            INDEXER_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            INDEXER_SERVER=http://localhost
            INDEXER_PORT=8980
            """
        )

    input_answers = ["N"]

    result = invoke(
        f"deploy {network}",
        cwd=cwd,
        input="\n".join(input_answers),
    )

    assert result.exit_code == 0 if network == "localnet" else 1
    verify(result.output, options=NamerFactory.with_parameters(has_env))
