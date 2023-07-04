import os
from unittest.mock import MagicMock

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.cli.deploy import BETANET, DEPLOYER_KEY, DISPENSER_KEY, LOCALNET, MAINNET, TESTNET, ensure_mnemonics
from algokit.core.conf import ALGOKIT_CONFIG
from algokit.core.deploy import ALGORAND_NETWORKS
from approvaltests.namer import NamerFactory
from click import ClickException
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke

CUSTOMNET = "customnet"


@pytest.fixture(autouse=True)
def _mock_validate_mnemonic(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.deploy._validate_mnemonic", return_value=None)


@pytest.fixture(autouse=True)
def mock_is_mainnet(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("algokit.cli.deploy.algokit_utils.is_mainnet", return_value=False)


@pytest.fixture(autouse=True)
def mock_is_localnet(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("algokit.cli.deploy.algokit_utils.is_localnet", return_value=LOCALNET)


# Your test can then simply use this fixture
def test_extract_mnemonics() -> None:
    # Check when environment variables are not set
    if DEPLOYER_KEY in os.environ:
        del os.environ[DEPLOYER_KEY]
    if DISPENSER_KEY in os.environ:
        del os.environ[DISPENSER_KEY]
    with pytest.raises(ClickException):
        ensure_mnemonics(skip_mnemonics_prompts=True)

    # Set environment variables for the test
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"
    os.environ[DISPENSER_KEY] = "test_dispenser_mnemonic"

    # Test extraction with skip_mnemonics_prompts=True
    ensure_mnemonics(skip_mnemonics_prompts=True)

    # Assert that the environment variables are not changed
    assert os.environ[DEPLOYER_KEY] == "test_deployer_mnemonic"
    assert os.environ[DISPENSER_KEY] == "test_dispenser_mnemonic"

    # Clean up environment variables
    del os.environ[DEPLOYER_KEY]
    del os.environ[DISPENSER_KEY]


# Approvals tests for deploy command
@pytest.mark.parametrize("network", ["", LOCALNET, TESTNET, MAINNET, BETANET, CUSTOMNET])
def test_deploy_no_algokit_toml(network: str, tmp_path_factory: TempPathFactory, mock_is_localnet: MagicMock) -> None:
    mock_is_localnet.return_value = network == LOCALNET
    if network != LOCALNET:
        os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"

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
    network: str, tmp_path_factory: TempPathFactory, mock_is_localnet: MagicMock
) -> None:
    mock_is_localnet.return_value = network == LOCALNET
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


@pytest.mark.parametrize("network", [BETANET, CUSTOMNET])
def test_deploy_generic_env(network: str, tmp_path_factory: TempPathFactory, mock_is_localnet: MagicMock) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    mock_is_localnet.return_value = network == LOCALNET
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"

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
    generic_env: bool, tmp_path_factory: TempPathFactory, mock_is_localnet: MagicMock  # noqa: FBT001
) -> None:
    mock_is_localnet.return_value = False
    cwd = tmp_path_factory.mktemp("cwd")
    network = TESTNET
    custom_folder = cwd / "custom_folder"
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"

    (custom_folder).mkdir()
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
    result = invoke(f"deploy {network} --project-dir={path}", cwd=cwd, input="\n".join(input_answers))

    assert result.exit_code == 0 if network == LOCALNET else 1
    verify(result.output, options=NamerFactory.with_parameters(generic_env))


@pytest.mark.parametrize("has_env", [True, False])
def test_deploy_custom_network_env(
    has_env: bool, tmp_path_factory: TempPathFactory, mock_is_localnet: MagicMock  # noqa: FBT001
) -> None:
    mock_is_localnet.return_value = False
    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"
    network = CUSTOMNET

    (cwd / ALGOKIT_CONFIG).write_text(f"[deploy.{network}]\ncommand = \"python -c print('HelloWorld')\"\n")

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
def test_deploy_custom_deploy_command(
    network: str, tmp_path_factory: TempPathFactory, mock_is_mainnet: MagicMock, mock_is_localnet: MagicMock
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    os.environ[DEPLOYER_KEY] = "test_deployer_mnemonic"
    mock_is_mainnet.return_value = network == MAINNET
    mock_is_localnet.return_value = network == LOCALNET

    custom_command = 'python -c print("HelloWorld")'
    if network == CUSTOMNET:
        (cwd / f".env.{network}").write_text(
            f"""
                ALGOD_SERVER={ALGORAND_NETWORKS[TESTNET]['ALGOD_SERVER']}
            """
        )

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
