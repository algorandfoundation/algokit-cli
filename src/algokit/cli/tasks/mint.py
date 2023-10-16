import logging
import math
from pathlib import Path

import click

from algokit.cli.tasks.utils import (
    get_account_with_private_key,
    get_asset_explorer_url,
    get_transaction_explorer_url,
    load_algod_client,
)
from algokit.core.tasks.ipfs import get_web3_storage_api_key
from algokit.core.tasks.mint.mint import MetadataStandard, mint_token
from algokit.core.tasks.mint.models import TokenMetadata

logger = logging.getLogger(__name__)


def _validate_inputs(total: int, decimals: int) -> None:
    # Validate total and decimals
    if not (total == 1 or (total % 10 == 0 and total != 0)):
        raise click.ClickException("Total must be 1 or a power of 10 larger than 1 (10, 100, 1000, ...).")
    if not ((total == 1 and decimals == 0) or (total != 1 and decimals == int(math.log10(total)))):
        raise click.ClickException(
            "Number of digits after the decimal point must be 0 for a pure NFT, or "
            "equal to the logarithm in base 10 of total number of units for a fractional NFT."
        )


@click.command(
    name="mint",
    help="Mint a new fungible or non-fungible assets on Algorand.",
)
@click.option(
    "--creator",
    "-r",
    required=True,
    prompt="Please enter the address or alias of the asset creator",
    help="Address or alias of the asset creator.",
    type=click.STRING,
)
@click.option(
    "--asset-name",
    type=click.STRING,
    required=True,
    prompt="Please enter the asset name",
    help="Asset name.",
)
@click.option(
    "--unit-name",
    type=click.STRING,
    required=True,
    prompt="Please enter the unit name",
    help="Unit name of the asset.",
)
@click.option(
    "--total",
    type=click.INT,
    required=True,
    prompt=(
        "Please enter the total supply. Set 1 for a pure NFT, or a power of 10 "
        "larger than 1 (10, 100, 1000, ...) for a fractional NFT."
    ),
    help=(
        "Total supply of the asset. Set 1 for a pure NFT, or a power of 10 "
        "larger than 1 (10, 100, 1000, ...) for a fractional NFT."
    ),
)
@click.option(
    "--decimals",
    type=click.INT,
    required=False,
    prompt="""Please enter the number of decimals. Set 0 for a pure NFT,
        or equal to the logarithm in base 10 of total supply for a fractional NFT.""",
    help="""Number of decimals. Set 0 for a pure NFT, ",
        "or equal to the logarithm in base 10 of total supply for a fractional NFT.""",
)
@click.option(
    "--image-path",
    "image_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    prompt="Please enter the path to the ARC19 compliant asset metadata file to be uploaded to IPFS",
    help="Path to the ARC19 compliant asset metadata file to be uploaded to IPFS.",
    required=True,
)
@click.option(
    "--token-metadata-path",
    "token_metadata_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    help="""Path to the ARC19 compliant asset metadata file to be uploaded to IPFS. If not provided,
        a default metadata object will be generated automatically based on asset-name, decimals and image.
        For more details refer to https://arc.algorand.foundation/ARCs/arc-0003#json-metadata-file-schema.""",
    default=None,
    required=False,
)
@click.option(
    "--arc",
    "metadata_standard",
    type=click.Choice([standard.value for standard in MetadataStandard]),
    prompt="Please enter the ARC standard to use (arc19 or arc3)",
    default=MetadataStandard.ARC19.value,
    required=False,
    help="ARC standard to use. Refers to `arc19` by default.",
)
@click.option(
    "-n",
    "--network",
    type=click.Choice(["localnet", "testnet", "mainnet"]),
    prompt="Please enter the network to use",
    default="localnet",
    required=False,
    help="Network to use. Refers to `localnet` by default.",
)
def mint(  # noqa: PLR0913
    creator: str,
    asset_name: str,
    unit_name: str,
    total: int,
    decimals: int,
    image_path: Path,
    token_metadata_path: Path | None,
    metadata_standard: str,
    network: str,
) -> None:
    _validate_inputs(total, decimals)

    creator_account = get_account_with_private_key(creator)

    web3_storage_api_key = get_web3_storage_api_key()
    if not web3_storage_api_key:
        raise click.ClickException("You are not logged in! Please login using `algokit ipfs login`.")

    client = load_algod_client(network)

    token_metadata = TokenMetadata.from_json_file(token_metadata_path)
    if not token_metadata_path:
        token_metadata.name = asset_name
        token_metadata.decimals = decimals

    is_mutable = (
        True
        if metadata_standard
        == MetadataStandard.ARC19.value  # The whole point of ARC19 is mutability, so we don't need to ask the user
        else click.confirm("Would you like to set `manager` field on your ARC3 asset configuration metadata?")
    )

    asset_id, txn_id = mint_token(
        client=client,
        api_key=web3_storage_api_key,
        creator_account=creator_account,
        token_metadata=token_metadata,
        image_path=image_path,
        unit_name=unit_name,
        asset_name=asset_name,
        metadata_standard=metadata_standard,
        is_mutable=is_mutable,
        total=total,
    )

    click.echo("Successfully minted asset!")
    click.echo(f"Browse your asset at: {get_asset_explorer_url(asset_id, network)}")
    click.echo(f"Check transaction status at: {get_transaction_explorer_url(txn_id, network)}")
