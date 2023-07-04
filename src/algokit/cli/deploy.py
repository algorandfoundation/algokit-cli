import logging
import os
from pathlib import Path

import algokit_utils
import click

from algokit.core import constants, proc
from algokit.core.deploy import load_deploy_command, load_deploy_config

logger = logging.getLogger(__name__)


ALGORAND_MNEMONIC_LENGTH = 25
DEPLOYER_KEY = "DEPLOYER_MNEMONIC"
DISPENSER_KEY = "DISPENSER_MNEMONIC"


def _validate_mnemonic(value: str) -> str:
    try:
        algokit_utils.get_account_from_mnemonic(value)
    except Exception as ex:
        raise click.UsageError("Invalid mnemonic") from ex
    return value


def ensure_mnemeonics(*, skip_mnemonics_prompts: bool) -> None:
    """
    Extract environment variables, prompt user if needed.

    :param skip_mnemonics_prompts: A boolean indicating if user prompt should be skipped.
    :param network: The name of the network ('localnet', 'testnet', 'mainnet', etc.)
    :return: A tuple containing deployer_mnemonic and dispenser_mnemonic.
    """
    deployer_mnemonic = os.getenv(DEPLOYER_KEY)
    dispenser_mnemonic = os.getenv(DISPENSER_KEY)

    if deployer_mnemonic:
        _validate_mnemonic(deployer_mnemonic)
    else:
        if skip_mnemonics_prompts:
            raise click.ClickException(f"Error: missing {DEPLOYER_KEY} environment variable")
        deployer_mnemonic = click.prompt("deployer-mnemonic", hide_input=True, value_proc=_validate_mnemonic)

    if dispenser_mnemonic:
        _validate_mnemonic(dispenser_mnemonic)
    elif not skip_mnemonics_prompts:
        use_dispenser = click.confirm("Do you want to use a dispenser account?", default=False)
        if use_dispenser:
            dispenser_mnemonic = click.prompt("dispenser-mnemonic", hide_input=True, value_proc=_validate_mnemonic)

    # TODO: fix this to write to os.environ instead
    return deployer_mnemonic, dispenser_mnemonic


@click.command("deploy")
@click.argument("network_or_environment_name", default=constants.LOCALNET)
@click.option(
    "custom_deploy_command",
    "--custom-deploy-command",
    type=str,
    default=None,
    help="Custom deploy command. If not provided, will load the deploy command from .algokit.toml file.",
)
@click.option(
    "skip_mnemonics_prompts",
    "--ci",
    is_flag=True,
    default=False,
    help="Skip interactive prompt for mnemonics, expects them to be set as environment variables.",
)
@click.option(
    "is_production_environment",
    "--prod",
    is_flag=True,
    default=False,
    help="Skip warning prompt for deployments to a mainnet.",
)
@click.option(
    "project_dir",
    "--project-dir",
    type=click.Path(exists=True, readable=True, file_okay=False, resolve_path=True, path_type=Path),
    default=".",
    help="Specify the project directory. If not provided, current working directory will be used.",
)
def deploy_command(
    *,
    network_or_environment_name: str,
    custom_deploy_command: str,
    skip_mnemonics_prompts: bool,
    is_production_environment: bool,
    project_dir: Path,
) -> None:
    """Deploy smart contracts from AlgoKit compliant repository."""
    with load_deploy_config(network_or_environment_name, project_dir):
        logger.info("Loaded deployment configuration.")
        client = algokit_utils.network_clients.get_algod_client()
        network_name = client.suggested_params().gen
        logger.info(
            f"Starting deployment process on {network_name} network..."
        )  # TODO: do we need this? makes for potentially 3x suggested_params calls
        if not is_production_environment and algokit_utils.is_mainnet(client):
            click.confirm(
                "You are about to deploy to the MainNet. Are you sure you want to continue?",
                abort=True,
            )

        logger.info(f"Project directory: {project_dir}")

        command = custom_deploy_command or load_deploy_command(network_name=network_name, project_dir=project_dir)
        logger.info(f"Using deploy command: {command}")

        if not algokit_utils.is_localnet(client):
            # TODO: this should write to os.environ
            ensure_mnemeonics(skip_mnemonics_prompts=skip_mnemonics_prompts)

        logger.info("Deploying smart contracts from AlgoKit compliant repository 🚀")
        try:
            proc.run(command.split(), cwd=project_dir, stdout_log_level=logging.INFO)
        except Exception as ex:
            raise click.ClickException(f"Failed to execute deploy command '{command}'.") from ex
