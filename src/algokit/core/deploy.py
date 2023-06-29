# 1. User can call algokit deploy to different networks
# 2. By default algokit cli contains configs for testnet and mainnet
# 3. User can overwrite them by creating a config file in the project root


import logging
import os
import sys
from pathlib import Path

import click
import httpx
from dotenv import dotenv_values

from algokit.core import proc
from algokit.core.conf import get_algokit_config
from algokit.core.constants import ALGOKIT_CONFIG, ALGORAND_NETWORKS, AlgorandNetworkConfiguration

if sys.version_info >= (3, 11):
    pass
else:
    pass

logger = logging.getLogger(__name__)


def get_genesis_network_name(deploy_config: dict) -> str | None:
    """
    Get the network name from the genesis block.
    :param deploy_config: Deploy configuration.
    :return: Network name.
    """

    algod_server = deploy_config.get("ALGOD_SERVER")

    if not algod_server:
        raise click.ClickException("Missing ALGOD_SERVER in deploy configuration.")

    try:
        genesis_response = httpx.get(f"{algod_server}/genesis")
        genesis_response.raise_for_status()
        return genesis_response.json()["network"] if genesis_response.status_code == 200 else None  # noqa: PLR2004
    except httpx.HTTPError:
        logger.warning(f"Failed to load network name from {algod_server} due to HTTP error.", exc_info=True)
        return None


def load_deploy_config(network: str, project_dir: Path) -> dict:
    """
    Load the deploy configuration for the given network.
    :param network: Network name.
    :param project_dir: Project directory path.
    :return: Deploy configuration.
    """

    env_file_path = project_dir / f".env.{network}"
    if not env_file_path.exists():
        if network in ALGORAND_NETWORKS:
            logger.info(f"No .env file found at {env_file_path}, loading default configuration for {network}.")
            return dict(ALGORAND_NETWORKS.get(network, {}))

        raise click.ClickException(f"No .env file found at {env_file_path}")

    # Extract network configuration
    network_config = dotenv_values(env_file_path, verbose=True, interpolate=True)

    # Fill missing keys with empty strings
    for required_key in list(AlgorandNetworkConfiguration.__annotations__.keys()):
        if required_key not in network_config:
            logger.warning(f"Warning: {required_key} is missing, filling with an empty string.")
            network_config[required_key] = ""

    return network_config


def load_deploy_command(network_name: str, project_dir: Path) -> str:
    """
    Load the deploy command for the given network from .algokit.toml file.
    :param network_name: Network name.
    :param project_dir: Project directory path.
    :return: Deploy command.
    """

    # Load and parse the TOML configuration file
    config = get_algokit_config(project_dir)

    if not config:
        raise click.ClickException(
            f"Couldn't load {ALGOKIT_CONFIG} file. Ensure deploy command is specified, either via "
            f"--custom-deploy-command or inside {ALGOKIT_CONFIG} file."
        )

    # Extract the deploy command for the given network
    try:
        return str(config["deploy"][network_name]["command"])
    except KeyError:
        raise click.ClickException(f"Deploy command is not specified in '{ALGOKIT_CONFIG}' file.") from None


def execute_deploy_command(command: str, deploy_config: dict, project_dir: Path | None) -> None:
    """
    Execute the deploy command.
    :param command: Deploy command.
    :param deploy_config: Deploy configuration.
    :param project_dir: Project directory path.
    """

    # Parse the deploy command
    try:
        # Get a copy of the current environment variables
        env = os.environ.copy()

        # Update the environment with custom variables from network_config
        env.update({key.upper(): str(value) for key, value in deploy_config.items()})

        proc.run(command.split(), env=env, cwd=project_dir or Path.cwd(), stdout_log_level=logging.INFO)
    except Exception as ex:
        raise click.ClickException(f"Failed to execute deploy command '{command}'.") from ex
