# 1. User can call algokit deploy to different networks
# 2. By default algokit cli contains configs for testnet and mainnet
# 3. User can overwrite them by creating a config file in the project root
import contextlib
import logging
import os
from pathlib import Path
from typing import cast, Iterator

import click
import httpx
from dotenv import dotenv_values, load_dotenv
import algokit_utils

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config
from algokit.core.constants import ALGORAND_NETWORKS

logger = logging.getLogger(__name__)


def get_genesis_network_name(deploy_config: dict[str, str]) -> str | None:
    """
    Get the network name from the genesis block.
    :param deploy_config: Deploy configuration.
    :return: Network name.
    """


    algod_server = deploy_config.get("ALGOD_SERVER")
    port = deploy_config.get("ALGOD_PORT")
    token = deploy_config.get("ALGOD_TOKEN")

    if not algod_server:
        raise click.ClickException("Missing ALGOD_SERVER in deploy configuration.")
    if port:
        algod_authority = f"{algod_server}:{port}"
    else:
        algod_authority = algod_server

    try:
        headers = {"X-Algo-API-Token": token} if token else None
        genesis_response = httpx.get(f"{algod_authority}/genesis", headers=headers)
        genesis_response.raise_for_status()
        return genesis_response.json()["network"] if genesis_response.status_code == httpx.codes.OK else None
    except httpx.HTTPError:
        logger.warning(f"Failed to load network name from {algod_server} due to HTTP error.", exc_info=True)
        return None
    except KeyError:
        logger.warning(f"Failed to load network name from {algod_server} due to missing 'network' key.", exc_info=True)
        return None
    except Exception:
        logger.warning(f"Failed to load network name from {algod_server}.", exc_info=True)
        return None


@contextlib.contextmanager
def load_deploy_config(name: str, project_dir: Path) -> Iterator[None]:
    """
    Load the deploy configuration for the given network.
    :param name: Network name.
    :param project_dir: Project directory path.
    """
    current_env = os.environ.copy()
    specific_env_path = project_dir / f".env.{name}"
    try:
        if default_config := ALGORAND_NETWORKS.get(name):
            os.environ.update(cast(dict[str, str], default_config))
        elif not specific_env_path.exists():
            # if it's not a well-known network name, then we expect the specific env file to exist
            raise click.ClickException(f"{name} is not a known network, and no {specific_env_path} file")

        for path in [project_dir / ".env", specific_env_path]:
            if path.exists():
                load_dotenv(path, verbose=True, override=True)
        yield
    finally:
        os.environ.update(current_env)


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
