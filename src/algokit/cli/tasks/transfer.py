import logging
from typing import TYPE_CHECKING

import click
from algokit_utils import (
    TransferAssetParameters,
    TransferParameters,
    transfer_asset,
)
from algokit_utils import (
    transfer as transfer_algos,
)

from algokit.cli.common.constants import AlgorandNetwork, ExplorerEntityType
from algokit.cli.common.utils import get_explorer_url
from algokit.cli.tasks.utils import (
    get_account_with_private_key,
    get_address,
    get_asset_decimals,
    load_algod_client,
    validate_address,
    validate_balance,
)

if TYPE_CHECKING:
    from algosdk.transaction import AssetTransferTxn, PaymentTxn

logger = logging.getLogger(__name__)

# TODO: upon algokit nfd lookup being implemented receiver will also allow nfd lookups


@click.command(name="transfer", help="""Transfer algos or assets from one account to another.""")
@click.option("--sender", "-s", type=click.STRING, help="Address or alias of the sender account.", required=True)
@click.option(
    "--receiver",
    "-r",
    type=click.STRING,
    help="Address or alias to an account that will receive the asset(s).",
    required=True,
)
@click.option(
    "--asset",
    "--id",
    "asset_id",
    type=click.INT,
    help="Asset ID to transfer. Defaults to 0 (Algo).",
    default=0,
    required=False,
)
@click.option("--amount", "-a", type=click.INT, help="Amount to transfer.", required=True)
@click.option(
    "--whole-units",
    "whole_units",
    is_flag=True,
    type=click.BOOL,
    help=(
        "Use whole units (Algos | ASAs) instead of smallest divisible units (for example, microAlgos). "
        "Disabled by default."
    ),
    default=False,
    required=False,
)
@click.option(
    "-n",
    "--network",
    type=click.Choice([choice.value for choice in AlgorandNetwork]),
    default=AlgorandNetwork.LOCALNET,
    required=False,
    help=f"Network to use. Refers to `{AlgorandNetwork.LOCALNET}` by default.",
)
def transfer(  # noqa: PLR0913
    *,
    sender: str,
    receiver: str,
    asset_id: int,
    amount: int,
    whole_units: bool,
    network: AlgorandNetwork,
) -> None:
    # Load addresses and accounts from mnemonics or aliases
    sender_account = get_account_with_private_key(sender)
    receiver_address = get_address(receiver)

    # Get algod client
    algod_client = load_algod_client(network)

    # Convert amount to whole units if specified
    if whole_units:
        amount = amount * (10 ** get_asset_decimals(asset_id, algod_client))

    # Validate inputs
    validate_address(receiver_address)
    validate_balance(algod_client, sender_account, asset_id, amount)
    validate_balance(algod_client, receiver_address, asset_id)

    # Transfer algos or assets depending on asset_id
    txn_response: PaymentTxn | AssetTransferTxn | None = None
    try:
        if asset_id == 0:
            txn_response = transfer_algos(
                algod_client,
                TransferParameters(to_address=receiver_address, from_account=sender_account, micro_algos=amount),
            )
        else:
            txn_response = transfer_asset(
                algod_client,
                TransferAssetParameters(
                    from_account=sender_account,
                    to_address=receiver_address,
                    amount=amount,
                    asset_id=asset_id,
                ),
            )

        if not txn_response:
            raise click.ClickException("Failed to perform transfer")

        txn_url = get_explorer_url(
            identifier=txn_response.get_txid(),  # type: ignore[no-untyped-call]
            network=network,
            entity_type=ExplorerEntityType.TRANSACTION,
        )
        click.echo(f"Successfully performed transfer. See details at {txn_url}")

    except Exception as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException("Failed to perform transfer") from err
