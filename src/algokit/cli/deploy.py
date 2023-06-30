import logging
import os
from pathlib import Path

import click

from algokit.core.constants import DEFAULT_NETWORKS, DEPLOYER_KEY, DISPENSER_KEY, LOCALNET, MAINNET
from algokit.core.deploy import (
    execute_deploy_command,
    get_genesis_network_name,
    load_deploy_command,
    load_deploy_config,
)

logger = logging.getLogger(__name__)


def extract_mnemonics(skip_mnemonics_prompts: bool, network: str) -> tuple[str | None, str | None]:  # noqa: FBT001
    """
    Extract environment variables, prompt user if needed.

    :param skip_mnemonics_prompts: A boolean indicating if user prompt should be skipped.
    :param network: The name of the network ('localnet', 'testnet', 'mainnet', etc.)
    :return: A tuple containing deployer_mnemonic and dispenser_mnemonic.
    """
    deployer_mnemonic = os.environ.get(DEPLOYER_KEY, "")
    dispenser_mnemonic = os.environ.get(DISPENSER_KEY, None)

    is_not_localnet = network != LOCALNET
    is_deployer_mnemonic_empty = not skip_mnemonics_prompts and not deployer_mnemonic
    is_dispenser_mnemonic_empty = not skip_mnemonics_prompts and not dispenser_mnemonic

    if is_deployer_mnemonic_empty and is_not_localnet:
        deployer_mnemonic = click.prompt("deployer-mnemonic", hide_input=True)

    if (
        is_dispenser_mnemonic_empty
        and is_not_localnet
        and click.confirm("Do you want to use a dispenser account?", default=False)
    ):
        dispenser_mnemonic = click.prompt("dispenser-mnemonic", hide_input=True)

    return deployer_mnemonic, dispenser_mnemonic


@click.command("deploy")
@click.argument(
    "network", type=str, default=LOCALNET, required=True, callback=(lambda _ctx, _param, value: value.lower())
)
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
def deploy_command(
    network: str,
    custom_deploy_command: str,
    skip_mnemonics_prompts: bool,  # noqa: FBT001
    is_production_environment: bool,  # noqa: FBT001
) -> None:
    """Deploy smart contracts from AlgoKit compliant repository."""
    logger.info(f"Starting deployment process on {network} network...")

    project_dir = Path.cwd()
    logger.info(f"Project directory: {project_dir}")

    deploy_command = custom_deploy_command or load_deploy_command(network_name=network, project_dir=project_dir)
    logger.info(f"Using deploy command: {deploy_command}")

    deployer_mnemonic, dispenser_mnemonic = extract_mnemonics(skip_mnemonics_prompts, network)

    if not deployer_mnemonic and network != LOCALNET:
        raise click.ClickException("Error: Deployer Mnemonic must be provided via env var or via cli input.")

    deploy_config = load_deploy_config(network, project_dir)
    logger.info("Loaded deployment configuration.")

    if not is_production_environment:
        network_name = network if network in DEFAULT_NETWORKS else get_genesis_network_name(deploy_config) or network

        if MAINNET in network_name:
            click.confirm(
                "You are about to deploy to the MainNet. Are you sure you want to continue?",
                abort=True,
            )

    deploy_config[DEPLOYER_KEY] = deployer_mnemonic
    if dispenser_mnemonic:
        deploy_config[DISPENSER_KEY] = dispenser_mnemonic

    logger.info("Deploying smart contracts from AlgoKit compliant repository 🚀")
    execute_deploy_command(command=deploy_command, deploy_config=deploy_config, project_dir=project_dir)
