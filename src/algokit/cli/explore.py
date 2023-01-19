from typing import TypedDict
from urllib.parse import urlencode

import click

from algokit.core.sandbox import DEFAULT_ALGOD_PORT, DEFAULT_ALGOD_SERVER, DEFAULT_ALGOD_TOKEN, DEFAULT_INDEXER_PORT


class NetworkConfigurationRequired(TypedDict):
    algod_url: str
    indexer_url: str


class NetworkConfiguration(NetworkConfigurationRequired, total=False):
    algod_port: int
    algod_token: str

    indexer_port: int
    indexer_token: str


NETWORKS: dict[str, NetworkConfiguration] = {
    "localnet": {
        "algod_url": DEFAULT_ALGOD_SERVER,
        "indexer_url": DEFAULT_ALGOD_SERVER,
        "algod_port": DEFAULT_ALGOD_PORT,
        "algod_token": DEFAULT_ALGOD_TOKEN,
        "indexer_port": DEFAULT_INDEXER_PORT,
        "indexer_token": DEFAULT_ALGOD_TOKEN,
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
    click.launch(url)
