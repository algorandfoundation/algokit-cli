import logging
import os
from pathlib import Path

import algokit_utils
import click

from algokit.core import constants, proc
from algokit.core.deploy import get_genesis_network_name, load_deploy_command, load_deploy_config

logger = logging.getLogger(__name__)


ALGORAND_MNEMONIC_LENGTH = 25


def _validate_mnemonic(value: str) -> str:
    try:
        algokit_utils.get_account_from_mnemonic(value)
    except Exception as ex:
        raise click.UsageError("Invalid mnemonic") from ex
    return value


def extract_mnemonics(*, skip_mnemonics_prompts: bool, network: str) -> tuple[str, str | None]:
    """
    Extract environment variables, prompt user if needed.

    :param skip_mnemonics_prompts: A boolean indicating if user prompt should be skipped.
    :param network: The name of the network ('localnet', 'testnet', 'mainnet', etc.)
    :return: A tuple containing deployer_mnemonic and dispenser_mnemonic.
    """
    deployer_mnemonic = os.getenv(constants.DEPLOYER_KEY)
    dispenser_mnemonic = os.getenv(constants.DISPENSER_KEY)

    if network != constants.LOCALNET:
        if deployer_mnemonic:
            _validate_mnemonic(deployer_mnemonic)
        else:
            if skip_mnemonics_prompts:
                raise click.ClickException(f"Error: missing {constants.DEPLOYER_KEY} environment variable")
            deployer_mnemonic = click.prompt("deployer-mnemonic", hide_input=True, value_proc=_validate_mnemonic)

        if dispenser_mnemonic:
            _validate_mnemonic(dispenser_mnemonic)
        elif not skip_mnemonics_prompts:
            use_dispenser = click.confirm("Do you want to use a dispenser account?", default=False)
            if use_dispenser:
                dispenser_mnemonic = click.prompt("dispenser-mnemonic", hide_input=True, value_proc=_validate_mnemonic)

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
    deploy_config = load_deploy_config(network_or_environment_name, project_dir)
    network_name = get_genesis_network_name(deploy_config) or network_or_environment_name

    logger.info(f"Starting deployment process on {network_name} network...")

    logger.info(f"Project directory: {project_dir}")

    command = custom_deploy_command or load_deploy_command(network_name=network_name, project_dir=project_dir)
    logger.info(f"Using deploy command: {command}")

    deployer_mnemonic, dispenser_mnemonic = extract_mnemonics(
        skip_mnemonics_prompts=skip_mnemonics_prompts, network=network
    )

    logger.info("Loaded deployment configuration.")

    if not is_production_environment:
        if network in constants.ALGORAND_NETWORKS:
            network_name = network
        else:
            pass

        if constants.MAINNET in network_name:
            click.confirm(
                "You are about to deploy to the MainNet. Are you sure you want to continue?",
                abort=True,
            )

    deploy_config[constants.DEPLOYER_KEY] = deployer_mnemonic
    if dispenser_mnemonic:
        deploy_config[constants.DISPENSER_KEY] = dispenser_mnemonic

    logger.info("Deploying smart contracts from AlgoKit compliant repository 🚀")
    try:
        proc.run(command.split(), env=deploy_config, cwd=project_dir, stdout_log_level=logging.INFO)
    except Exception as ex:
        raise click.ClickException(f"Failed to execute deploy command '{command}'.") from ex
