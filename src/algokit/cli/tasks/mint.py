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
from algokit.core.tasks.mint.mint import mint_token
from algokit.core.tasks.mint.models import TokenMetadata

logger = logging.getLogger(__name__)

MAX_UNIT_NAME_BYTE_LENGTH = 8
MAX_ASSET_NAME_BYTE_LENGTH = 32


def _validate_supply(total: int, decimals: int) -> None:
    # Validate total and decimals
    if not (total == 1 or (total % 10 == 0 and total != 0)):
        raise click.ClickException("Total must be 1 or a power of 10 larger than 1 (10, 100, 1000, ...).")
    if not ((total == 1 and decimals == 0) or (total != 1 and decimals == int(math.log10(total)))):
        raise click.ClickException(
            "Number of digits after the decimal point must be 0 for a pure NFT, or "
            "equal to the logarithm in base 10 of total number of units for a fractional NFT."
        )


def _validate_unit_name(context: click.Context, param: click.Parameter, value: str) -> str:
    if len(value.encode("utf-8")) <= MAX_UNIT_NAME_BYTE_LENGTH:
        return value
    else:
        raise click.BadParameter(
            f"Unit name must be {MAX_UNIT_NAME_BYTE_LENGTH} bytes or less.", ctx=context, param=param
        )


def _validate_asset_name(context: click.Context, param: click.Parameter, value: str) -> str:
    if len(value.encode("utf-8")) <= MAX_ASSET_NAME_BYTE_LENGTH:
        return value
    else:
        raise click.BadParameter(
            f"Unit name must be {MAX_UNIT_NAME_BYTE_LENGTH} bytes or less.", ctx=context, param=param
        )


@click.command(
    name="mint",
    help="Mint a new fungible or non-fungible assets on Algorand.",
)
@click.option(
    "--creator",
    required=True,
    prompt="Provide the address or alias of the asset creator",
    help="Address or alias of the asset creator.",
    type=click.STRING,
)
@click.option(
    "-n",
    "--name",
    "asset_name",
    type=click.STRING,
    required=True,
    callback=_validate_asset_name,
    prompt="Provide the asset name",
    help="Asset name.",
)
@click.option(
    "-u",
    "--unit",
    "unit_name",
    type=click.STRING,
    required=True,
    callback=_validate_unit_name,
    prompt="Provide the unit name",
    help="Unit name of the asset.",
)
@click.option(
    "-t",
    "--total",
    type=click.INT,
    required=False,
    default=1,
    prompt="Provide the total supply",
    help="Total supply of the asset. Defaults to 1.",
)
@click.option(
    "-d",
    "--decimals",
    type=click.INT,
    required=False,
    default=0,
    prompt="Provide the number of decimals",
    help="Number of decimals. Defaults to 0.",
)
@click.option(
    "-i",
    "--image",
    "image_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    prompt="Provide the path to the asset image file",
    help="Path to the asset image file to be uploaded to IPFS.",
    required=True,
)
@click.option(
    "-m",
    "--metadata",
    "token_metadata_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    help="""Path to the ARC19 compliant asset metadata file to be uploaded to IPFS. If not provided,
        a default metadata object will be generated automatically based on asset-name, decimals and image.
        For more details refer to https://arc.algorand.foundation/ARCs/arc-0003#json-metadata-file-schema.""",
    default=None,
    required=False,
)
@click.option(
    "--mutable/--immutable",
    type=click.BOOL,
    prompt="Would you like to make the asset mutable?",
    default=False,
    help="Whether the asset should be mutable or immutable. Refers to `ARC19` by default.",
)
@click.option(
    "--nft/--ft",
    "non_fungible",
    type=click.BOOL,
    prompt="Validate asset as NFT? Checks values of `total` and `decimals` as per ARC3 if set to True.",
    default=False,
    help="""Whether the asset should be validated as NFT or FT. Refers to NFT by default and validates canonical
    definitions of pure or fractional NFTs as per ARC3 standard.""",
)
@click.option(
    "-n",
    "--network",
    type=click.Choice(["localnet", "testnet", "mainnet"]),
    prompt="Provide the network to use",
    default="localnet",
    required=False,
    help="Network to use. Refers to `localnet` by default.",
)
def mint(  # noqa: PLR0913
    *,
    creator: str,
    asset_name: str,
    unit_name: str,
    total: int,
    decimals: int,
    image_path: Path,
    token_metadata_path: Path | None,
    mutable: bool,
    non_fungible: bool,
    network: str,
) -> None:
    if non_fungible:
        _validate_supply(total, decimals)

    creator_account = get_account_with_private_key(creator)

    web3_storage_api_key = get_web3_storage_api_key()
    if not web3_storage_api_key:
        raise click.ClickException("You are not logged in! Please login using `algokit ipfs login`.")

    client = load_algod_client(network)

    token_metadata = TokenMetadata.from_json_file(token_metadata_path)
    if not token_metadata_path:
        token_metadata.name = asset_name
        token_metadata.decimals = decimals

    asset_id, txn_id = mint_token(
        client=client,
        api_key=web3_storage_api_key,
        creator_account=creator_account,
        token_metadata=token_metadata,
        image_path=image_path,
        unit_name=unit_name,
        asset_name=asset_name,
        mutable=mutable,
        total=total,
    )

    click.echo("\nSuccessfully minted the asset!")
    click.echo(f"Browse your asset at: {get_asset_explorer_url(asset_id, network)}")
    click.echo(f"Check transaction status at: {get_transaction_explorer_url(txn_id, network)}")
