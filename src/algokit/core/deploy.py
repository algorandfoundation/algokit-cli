# 1. User can call algokit deploy to different networks
# 2. By default algokit cli contains configs for testnet and mainnet
# 3. User can overwrite them by creating a config file in the project root
import logging
import os
from pathlib import Path

import click
import httpx
from dotenv import load_dotenv

from algokit.core import sandbox
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


GITPOD_URL = os.getenv("GITPOD_WORKSPACE_URL")

LOCALNET_ALIASES = ("devnet", "sandnet", "dockernet")
LOCALNET = "localnet"
MAINNET = "mainnet"
BETANET = "betanet"
TESTNET = "testnet"

ALGORAND_NETWORKS: dict[str, dict[str, str]] = {
    LOCALNET: {
        "ALGOD_SERVER": sandbox.DEFAULT_ALGOD_SERVER,
        "ALGOD_PORT": str(sandbox.DEFAULT_ALGOD_PORT),
        "ALGOD_TOKEN": sandbox.DEFAULT_ALGOD_TOKEN,
        "INDEXER_SERVER": sandbox.DEFAULT_ALGOD_SERVER,
        "INDEXER_PORT": str(sandbox.DEFAULT_INDEXER_PORT),
        "INDEXER_TOKEN": sandbox.DEFAULT_ALGOD_TOKEN,
    }
    if not GITPOD_URL
    else {
        "ALGOD_SERVER": GITPOD_URL.replace("https://", f"https://{sandbox.DEFAULT_ALGOD_PORT}-"),
        "ALGOD_TOKEN": sandbox.DEFAULT_ALGOD_TOKEN,
        "INDEXER_SERVER": GITPOD_URL.replace("https://", f"https://{sandbox.DEFAULT_INDEXER_PORT}-"),
        "INDEXER_TOKEN": sandbox.DEFAULT_ALGOD_TOKEN,
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


def load_deploy_config(name: str, project_dir: Path) -> None:
    """
    Load the deploy configuration for the given network.
    :param name: Network name.
    :param project_dir: Project directory path.
    """
    specific_env_path = project_dir / f".env.{name}"
    # first, we load in any defaults if "name" is a known network name
    if default_config := ALGORAND_NETWORKS.get(name):
        # note we don't "update" here, if there is already an existing
        # environment variable we don't want to overwrite it with a network default,
        # so we just use `setdefault` instead
        for k, v in default_config.items():
            os.environ.setdefault(k, v)
    # if it's not a well-known network name, then we expect the specific env file to exist,
    # if it doesn't then fail fast here
    elif not specific_env_path.exists():
        raise click.ClickException(f"{name} is not a known network, and no {specific_env_path} file")

    # next we load in the .env file if it exists, and finally the .env.name specific file
    for path in [project_dir / ".env", specific_env_path]:
        if path.exists():
            # TODO: do we really want to override here?
            load_dotenv(path, verbose=True, override=True)


def load_deploy_command(name: str, project_dir: Path) -> str:
    """
    Load the deploy command for the given network/environment from .algokit.toml file.
    :param name: Network or environment name.
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
        return str(config["deploy"][name]["command"])
    except KeyError:
        raise click.ClickException(
            f"Deploy command for '{name}' is not specified in '{ALGOKIT_CONFIG}' file."
        ) from None
