# 1. User can call algokit deploy to different networks
# 2. By default algokit cli contains configs for testnet and mainnet
# 3. User can overwrite them by creating a config file in the project root


import configparser
import logging
import os
import sys
from pathlib import Path

import click

from algokit.core import proc
from algokit.core.bootstrap import ALGOKIT_CONFIG

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

logger = logging.getLogger(__name__)


def _generate_config(  # noqa: PLR0913
    algod_server: str,
    indexer_server: str,
    algod_token: str = "",
    algod_port: str = "",
    indexer_token: str = "",
    indexer_port: str = "",
) -> dict[str, str]:
    return {
        "ALGOD_TOKEN": algod_token,
        "ALGOD_SERVER": algod_server,
        "ALGOD_PORT": algod_port,
        "INDEXER_TOKEN": indexer_token,
        "INDEXER_SERVER": indexer_server,
        "INDEXER_PORT": indexer_port,
    }


REQUIRED_KEYS = [
    "ALGOD_TOKEN",
    "ALGOD_SERVER",
    "ALGOD_PORT",
    "INDEXER_TOKEN",
    "INDEXER_SERVER",
    "INDEXER_PORT",
]

DEPLOY_CONFIGS = {
    "localnet": _generate_config(
        algod_token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        algod_server="http://localhost",
        algod_port="4001",
        indexer_token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        indexer_server="http://localhost",
        indexer_port="8980",
    ),
    "testnet": _generate_config(
        algod_server="https://testnet-api.algonode.cloud",
        indexer_server="https://testnet-idx.algonode.cloud",
    ),
    "mainnet": _generate_config(
        algod_server="https://mainnet-api.algonode.cloud",
        indexer_server="https://mainnet-idx.algonode.cloud",
    ),
    "betanet": _generate_config(
        algod_server="https://betanet-api.algonode.cloud",
        indexer_server="https://betanet-idx.algonode.cloud",
    ),
}


def load_deploy_config(network: str, project_dir: Path) -> dict:
    """
    Parse the .env file if it exists and load configurations.
    :param network: Network name.
    :param project_dir: Project directory path.
    :return: A dictionary containing the configuration.
    """

    env_file_path = project_dir / ".env"
    if env_file_path.exists():
        config = configparser.ConfigParser()
        with env_file_path.open() as f:
            config.read_string("[config]\n" + f.read())

        # Extract network configuration
        network_config = {}
        prefix = f"{network.upper()}_"
        for key, value in config["config"].items():
            # Strip the network prefix from each key
            if key.startswith(prefix):
                new_key = key[len(prefix) :]
                network_config[new_key] = value

        # Fill missing keys with empty strings
        for required_key in REQUIRED_KEYS:
            if required_key not in network_config:
                logger.warning(f"Warning: {required_key} is missing, filling with an empty string.")
                network_config[required_key] = ""

        return network_config
    else:
        logger.info(f"No .env file found, loading default configuration for {network}.")
        return DEPLOY_CONFIGS.get(network, {})


def load_deploy_command(network_name: str, project_dir: Path) -> str:
    """
    Load the deploy command for the given network from .algokit.toml file.
    :param network_name: Network name.
    :param project_dir: Project directory path.
    :return: Deploy command.
    """

    # Load and parse the TOML configuration file
    config_path = project_dir / ALGOKIT_CONFIG
    try:
        config_content = config_path.read_text("utf-8")
    except FileNotFoundError:
        logger.debug(f"No {ALGOKIT_CONFIG} file found in the project directory.")
        raise click.ClickException(f"No {ALGOKIT_CONFIG} file found in the project directory.") from None

    try:
        config = tomllib.loads(config_content)
    except FileNotFoundError:
        raise click.ClickException(f"Configuration file '{config_path}' not found.") from None

    # Extract the deploy command for the given network
    try:
        return config["deploy"][network_name]["command"]
    except KeyError:
        raise click.ClickException(f"Configuration file '{config_path}' not found.") from None


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
