import logging
import math
from pathlib import Path

import click
from algosdk.error import AlgodHTTPError
from algosdk.util import algos_to_microalgos

from algokit.cli.common.constants import AlgorandNetwork, ExplorerEntityType
from algokit.cli.common.utils import get_explorer_url
from algokit.cli.tasks.utils import (
    get_account_with_private_key,
    load_algod_client,
    validate_balance,
)
from algokit.core.tasks.ipfs import (
    Web3StorageBadRequestError,
    Web3StorageForbiddenError,
    Web3StorageHttpError,
    Web3StorageInternalServerError,
    Web3StorageUnauthorizedError,
    get_web3_storage_api_key,
)
from algokit.core.tasks.mint.mint import mint_token
from algokit.core.tasks.mint.models import TokenMetadata

logger = logging.getLogger(__name__)

MAX_UNIT_NAME_BYTE_LENGTH = 8
MAX_ASSET_NAME_BYTE_LENGTH = 32
ASSET_MINTING_MBR = 0.2  # Algos, 0.1 for base account, 0.1 for asset creation


def _validate_supply(total: int, decimals: int) -> None:
    """
    Validate the total supply and decimal places of a token.

    Args:
        total (int): The total supply of the token.
        decimals (int): The number of decimal places for the token.

    Raises:
        click.ClickException: If the validation fails.
    """
    if not (total == 1 or (total % 10 == 0 and total != 0)):
        raise click.ClickException("Total must be 1 or a power of 10 larger than 1 (10, 100, 1000, ...).")
    if not ((total == 1 and decimals == 0) or (total != 1 and decimals == int(math.log10(total)))):
        raise click.ClickException(
            "Number of digits after the decimal point must be 0 for a pure NFT, or "
            "equal to the logarithm in base 10 of total number of units for a fractional NFT."
        )


def _validate_unit_name(context: click.Context, param: click.Parameter, value: str) -> str:
    """
    Validate the unit name by checking if its byte length is less than or equal to a predefined maximum value.

    Args:
        context (click.Context): The click context.
        param (click.Parameter): The click parameter.
        value (str): The value of the parameter.

    Returns:
        str: The value of the parameter if it passes the validation.
    """

    if len(value.encode("utf-8")) <= MAX_UNIT_NAME_BYTE_LENGTH:
        return value
    else:
        raise click.BadParameter(
            f"Unit name must be {MAX_UNIT_NAME_BYTE_LENGTH} bytes or less.", ctx=context, param=param
        )


def _validate_asset_name(context: click.Context, param: click.Parameter, value: str) -> str:
    """
    Validate the asset name by checking if its byte length is less than or equal to a predefined maximum value.

    Args:
        context (click.Context): The click context.
        param (click.Parameter): The click parameter.
        value (str): The value of the parameter.

    Returns:
        str: The value of the parameter if it passes the validation.
    """

    if len(value.encode("utf-8")) <= MAX_ASSET_NAME_BYTE_LENGTH:
        return value
    else:
        raise click.BadParameter(
            f"Unit name must be {MAX_UNIT_NAME_BYTE_LENGTH} bytes or less.", ctx=context, param=param
        )


@click.command(
    name="mint",
    help="Mint new fungible or non-fungible assets on Algorand.",
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
    type=click.Choice(AlgorandNetwork.to_list()),
    prompt="Provide the network to use",
    default=AlgorandNetwork.LOCALNET,
    required=False,
    help=f"Network to use. Refers to `{AlgorandNetwork.LOCALNET}` by default.",
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
    network: AlgorandNetwork,
) -> None:
    if non_fungible:
        _validate_supply(total, decimals)

    creator_account = get_account_with_private_key(creator)

    web3_storage_api_key = get_web3_storage_api_key()
    if not web3_storage_api_key:
        raise click.ClickException("You are not logged in! Please login using `algokit ipfs login`.")

    client = load_algod_client(network)
    validate_balance(
        client, creator_account, 0, algos_to_microalgos(ASSET_MINTING_MBR)  # type: ignore[no-untyped-call]
    )

    token_metadata = TokenMetadata.from_json_file(token_metadata_path)
    if not token_metadata_path:
        token_metadata.name = asset_name
        token_metadata.decimals = decimals
    try:
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
        click.echo(f"Browse your asset at: {get_explorer_url(asset_id, network, ExplorerEntityType.ASSET)}")
        click.echo(f"Check transaction status at: {get_explorer_url(txn_id, network, ExplorerEntityType.TRANSACTION)}")
    except (
        Web3StorageBadRequestError,
        Web3StorageUnauthorizedError,
        Web3StorageForbiddenError,
        Web3StorageInternalServerError,
        Web3StorageHttpError,
    ) as ex:
        logger.debug(ex)
        raise click.ClickException(repr(ex)) from ex
    except AlgodHTTPError as ex:
        raise click.ClickException(str(ex)) from ex
    except Exception as ex:
        logger.debug(ex, exc_info=True)
        raise click.ClickException("Failed to mint the asset!") from ex
