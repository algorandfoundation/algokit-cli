import logging

import click
from algokit_utils import AlgoAmount, AssetTransferParams, PaymentParams, SendAtomicTransactionComposerResults

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
from algokit.core.utils import get_algorand_client_for_network

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
    txn_response: SendAtomicTransactionComposerResults | None = None
    algorand = get_algorand_client_for_network(network)
    try:
        if asset_id == 0:
            txn_response = (
                algorand.new_group()
                .add_payment(
                    PaymentParams(
                        sender=sender_account.address,
                        receiver=receiver_address,
                        amount=AlgoAmount(micro_algo=amount),
                        signer=sender_account.signer,
                    )
                )
                .send()
            )
        else:
            txn_response = (
                algorand.new_group()
                .add_asset_transfer(
                    AssetTransferParams(
                        sender=sender_account.address,
                        receiver=receiver_address,
                        amount=amount,
                        asset_id=asset_id,
                        signer=sender_account.signer,
                    ),
                )
                .send()
            )

        txn_url = get_explorer_url(
            identifier=txn_response.tx_ids[0],
            network=network,
            entity_type=ExplorerEntityType.TRANSACTION,
        )
        click.echo(f"Successfully performed transfer. See details at {txn_url}")

    except Exception as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException("Failed to perform transfer") from err
