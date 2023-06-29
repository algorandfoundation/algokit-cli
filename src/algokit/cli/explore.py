import logging
from urllib.parse import urlencode

import click

from algokit.core.constants import ALGORAND_NETWORKS, AlgorandNetworkConfiguration

logger = logging.getLogger(__name__)


def get_dappflow_url(network: AlgorandNetworkConfiguration) -> str:
    # Filter out empty values
    dappflow_config = {key.lower(): value for key, value in network.items() if value}

    # Map keys to dappflow keys
    dappflow_config["algod_url"] = dappflow_config.pop("algod_server")
    dappflow_config["indexer_url"] = dappflow_config.pop("indexer_server")

    # Encode query string
    query_string = urlencode(dappflow_config)

    # Return dappflow url
    return f"https://app.dappflow.org/setup-config?{query_string}"


@click.command("explore", help="Explore the specified network in the browser using Dappflow.")
@click.argument("network", type=click.Choice(list(ALGORAND_NETWORKS)), default="localnet", required=False)
def explore_command(network: str) -> None:
    url = get_dappflow_url(ALGORAND_NETWORKS[network])
    logger.info(f"Opening {network} in https://app.dappflow.org using default browser")
    click.launch(url)
