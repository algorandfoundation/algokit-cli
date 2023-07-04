import logging
import os
from typing import TypedDict
from urllib.parse import urlencode

import click

from algokit.core.sandbox import DEFAULT_ALGOD_PORT, DEFAULT_ALGOD_SERVER, DEFAULT_ALGOD_TOKEN, DEFAULT_INDEXER_PORT

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
NETWORKS: dict[str, NetworkConfiguration] = {
    "localnet": {
        "algod_url": GITPOD_URL.replace("https://", "https://4001-") if GITPOD_URL else DEFAULT_ALGOD_SERVER,
        "indexer_url": GITPOD_URL.replace("https://", "https://8980-") if GITPOD_URL else DEFAULT_ALGOD_SERVER,
        "algod_port": 443 if GITPOD_URL else DEFAULT_ALGOD_PORT,
        "algod_token": DEFAULT_ALGOD_TOKEN,
        "indexer_port": 443 if GITPOD_URL else DEFAULT_INDEXER_PORT,
        "indexer_token": DEFAULT_ALGOD_TOKEN,
        "kmd_token": DEFAULT_ALGOD_TOKEN,
        "kmd_port": 443 if GITPOD_URL else DEFAULT_ALGOD_PORT + 1,
        "kmd_url": GITPOD_URL.replace("https://", "https://4002-") if GITPOD_URL else DEFAULT_ALGOD_SERVER,
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


def get_dappflow_url(network: NetworkConfiguration) -> str:
    query_string = urlencode(network)
    return f"https://app.dappflow.org/setup-config?{query_string}"


@click.command("explore", help="Explore the specified network in the browser using Dappflow.")
@click.argument("network", type=click.Choice(list(NETWORKS)), default="localnet", required=False)
def explore_command(network: str) -> None:
    url = get_dappflow_url(NETWORKS[network])
    logger.info(f"Opening {network} in https://app.dappflow.org using default browser")
    click.launch(url)
