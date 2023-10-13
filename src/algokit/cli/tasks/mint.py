import logging
from pathlib import Path

import click

from algokit.cli.tasks.utils import get_account_with_private_key, load_algod_client
from algokit.core.tasks.ipfs import get_web3_storage_api_key
from algokit.core.tasks.mint.arc19 import mint_arc19_token

logger = logging.getLogger(__name__)


@click.command(
    name="mint",
    help="Mint a new fungible or non-fungible asset on Algorand.",
)
@click.option(
    "--creator",
    "-r",
    required=True,
    help="Address or alias of the asset creator.",
    type=click.STRING,
)
@click.option(
    "--metadata-path",
    "metadata_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    help="Path to the ARC19 compliant asset metadata file to be uploaded to IPFS.",
    required=True,
)
@click.option(
    "--image-path",
    "image_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    help="Path to the ARC19 compliant asset metadata file to be uploaded to IPFS.",
    required=True,
)
@click.option(
    "-n",
    "--network",
    type=click.Choice(["localnet", "testnet", "mainnet"]),
    default="localnet",
    required=False,
    help="Network to use. Refers to `localnet` by default.",
)
def mint(creator: str, metadata_path: Path, image_path: Path, network: str) -> None:
    creator_account = get_account_with_private_key(creator)

    web3_storage_api_key = get_web3_storage_api_key()
    if not web3_storage_api_key:
        raise click.ClickException("You are not logged in! Please login using `algokit ipfs login`.")

    client = load_algod_client(network)
    mint_arc19_token(
        client,
        web3_storage_api_key,
        creator_account,
        metadata_path,
        image_path,
        unit_name="ALGO",
    )
