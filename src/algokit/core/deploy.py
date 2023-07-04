# 1. User can call algokit deploy to different networks
# 2. By default algokit cli contains configs for testnet and mainnet
# 3. User can overwrite them by creating a config file in the project root
import contextlib
import logging
import os
from collections.abc import Iterator
from pathlib import Path

import click
import httpx
from dotenv import load_dotenv

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config

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


DEFAULT_ALGOD_SERVER = "http://localhost"
DEFAULT_ALGOD_TOKEN = "a" * 64
GITPOD_URL = os.environ.get("GITPOD_WORKSPACE_URL")

DOCKERNET = "dockernet"
LOCALNET = "localnet"
MAINNET = "mainnet"
BETANET = "betanet"
TESTNET = "testnet"

ALGORAND_NETWORKS: dict[str, dict[str, str]] = {
    LOCALNET: {
        "ALGOD_SERVER": GITPOD_URL.replace("https://", "https://4001-") if GITPOD_URL else DEFAULT_ALGOD_SERVER,
        "INDEXER_SERVER": GITPOD_URL.replace("https://", "https://8980-") if GITPOD_URL else DEFAULT_ALGOD_SERVER,
        "ALGOD_PORT": str(443 if GITPOD_URL else 4001),
        "ALGOD_TOKEN": DEFAULT_ALGOD_TOKEN,
        "INDEXER_PORT": str(443 if GITPOD_URL else 8980),
        "INDEXER_TOKEN": DEFAULT_ALGOD_TOKEN,
    },
    TESTNET: {
        "ALGOD_SERVER": "https://testnet-api.algonode.cloud",
        "INDEXER_SERVER": "https://testnet-idx.algonode.cloud",
    },
    BETANET: {
        "ALGOD_SERVER": "https://betanet-api.algonode.cloud",
        "INDEXER_SERVER": "https://betanet-idx.algonode.cloud",
    },
    MAINNET: {
        "ALGOD_SERVER": "https://mainnet-api.algonode.cloud",
        "INDEXER_SERVER": "https://mainnet-idx.algonode.cloud",
    },
}


@contextlib.contextmanager
def load_deploy_config(name: str, project_dir: Path) -> Iterator[None]:
    """
    Load the deploy configuration for the given network.
    :param name: Network name.
    :param project_dir: Project directory path.
    """
    current_env = os.environ.copy()
    specific_env_path = project_dir / f".env.{name}"
    generic_env_path = project_dir / ".env"
    try:
        if default_config := ALGORAND_NETWORKS.get(name):
            os.environ.update(default_config)
        elif specific_env_path.exists():
            load_dotenv(specific_env_path, verbose=True, override=True)
        elif generic_env_path.exists():
            load_dotenv(generic_env_path, verbose=True, override=True)
        else:
            # if it's not a well-known network name, and no specific or generic env file exist
            raise click.ClickException(
                f"{name} is not a known network, and no {specific_env_path} or {generic_env_path} file found"
            )

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
