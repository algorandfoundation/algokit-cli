import logging
import os
from typing import TypedDict
from urllib.parse import urlencode

import click

from algokit.core.sandbox import DEFAULT_ALGOD_PORT, DEFAULT_ALGOD_SERVER, DEFAULT_ALGOD_TOKEN, DEFAULT_INDEXER_PORT
from algokit.core.utils import is_wsl

logger = logging.getLogger(__name__)


class NetworkConfigurationRequired(TypedDict):
    algod_url: str
    indexer_url: str


class NetworkConfiguration(NetworkConfigurationRequired, total=False):
    algod_port: int
    algod_token: str

    indexer_port: int
    indexer_token: str

    kmd_token: str
    kmd_url: str
    kmd_port: int


GITPOD_URL = os.environ.get("GITPOD_WORKSPACE_URL")
CODESPACE_NAME = os.environ.get("CODESPACE_NAME")

if GITPOD_URL:
    algod_url = GITPOD_URL.replace("https://", "https://4001-")
    indexer_url = GITPOD_URL.replace("https://", "https://8980-")
    kmd_url = GITPOD_URL.replace("https://", "https://4002-")
    algod_port = 443
    indexer_port = 443
    kmd_port = 443
elif CODESPACE_NAME:
    algod_url = f"https://{CODESPACE_NAME}-4001.app.github.dev"
    indexer_url = f"https://{CODESPACE_NAME}-8980.app.github.dev"
    kmd_url = f"https://{CODESPACE_NAME}-4002.app.github.dev"
    algod_port = 443
    indexer_port = 443
    kmd_port = 443
else:
    algod_url = DEFAULT_ALGOD_SERVER
    indexer_url = DEFAULT_ALGOD_SERVER
    kmd_url = DEFAULT_ALGOD_SERVER
    algod_port = DEFAULT_ALGOD_PORT
    indexer_port = DEFAULT_INDEXER_PORT
    kmd_port = DEFAULT_ALGOD_PORT + 1

NETWORKS: dict[str, NetworkConfiguration] = {
    "localnet": {
        "algod_url": algod_url,
        "indexer_url": indexer_url,
        "algod_port": algod_port,
        "algod_token": DEFAULT_ALGOD_TOKEN,
        "indexer_port": indexer_port,
        "indexer_token": DEFAULT_ALGOD_TOKEN,
        "kmd_token": DEFAULT_ALGOD_TOKEN,
        "kmd_port": kmd_port,
        "kmd_url": kmd_url,
    },  # TODO: query these instead of using constants
    "testnet": {
        "algod_url": "https://testnet-api.algonode.cloud",
        "indexer_url": "https://testnet-idx.algonode.cloud",
    },
    "mainnet": {
        "algod_url": "https://mainnet-api.algonode.cloud",
        "indexer_url": "https://mainnet-idx.algonode.cloud",
    },
}


def get_algokit_url(network: str) -> str:
    return f"https://explore.algokit.io/{network}"


def get_explore_url(network: str) -> str:
    if network == "localnet" and NETWORKS[network].get("algod_url") != DEFAULT_ALGOD_SERVER:
        query_string = urlencode(
            [
                (key, value)
                for key, value in NETWORKS[network].items()
                if key in ["algod_url", "algod_port", "indexer_url", "indexer_port", "kmd_url", "kmd_port"]
            ]
        )
        return f"{get_algokit_url(network)}?{query_string}"

    return get_algokit_url(network)


@click.command("explore", help="Explore the specified network using lora.")
@click.argument("network", type=click.Choice(list(NETWORKS)), default="localnet", required=False)
def explore_command(network: str) -> None:
    url = get_explore_url(network)
    logger.info(f"Opening {network} explorer in your default browser")

    if is_wsl():
        import webbrowser

        warning = (
            "Unable to open browser from WSL environment.\n"
            "Ensure 'wslu' is installed: (https://wslutiliti.es/wslu/install.html),\n"
            f"or open the URL manually: '{url}'."
        )
        try:
            if not webbrowser.open(url):
                logger.warning(warning)
        except Exception as e:
            logger.warning(warning, exc_info=e)
    else:
        click.launch(url)
