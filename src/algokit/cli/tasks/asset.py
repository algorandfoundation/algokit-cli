import logging

import algokit_utils
import click
from algokit_utils import Account, TransferAssetParameters, TransferParameters, transfer_asset
from algosdk.v2client.algod import AlgodClient
import algosdk.encoding

logger = logging.getLogger(__name__)


@click.command(name="transfer")
@click.option("--sender", "-s", help="Alias of the sender account")
@click.option("--receiver", "-r", help="Alias address or NFD poiting to an account that will receive the asset(s)")
@click.option("--asset", "-id", help="ASA asset id to transfer")
@click.option("--amount", "-a", help="Amount to transfer")
@click.option("--whole-units", help="Unit the provided amount is specified as.")
@click.option("--network", "-n", help="Network where the transfer will be executed localnet|testnet|mainnet")
def transfer(  # noqa: PLR0913
    # *, if we are using booleans
    sender: str,
    receiver: str,
    asset: int,
    amount: int,
    whole_units: bool,
    network: str,
    algod_client: AlgodClient,
) -> None:
    # if not whole_units then amount is micro-algos if whole_units then algos (use algoAmount to convert)
    if algosdk.encoding.is_valid_address(sender) is False:
        raise Exception("Sender account is invalid")

    if algosdk.encoding.is_valid_address(receiver) is False:
        raise Exception("Receiver account is invalid")

    from_account = Account(address=sender, private_key=mnemonic.to_private_key(mnemonic_phrase))

    # if whole_units:
    #     micro_algos = amount
    # else
    #     micro_algos = AlgoAmount

    if asset == 0:
        algokit_utils.transfer(
            algod_client, TransferParameters(to_address=receiver, from_account=from_account, micro_algos=amount)
        )
    else:
        transfer_asset(
            algod_client,
            TransferAssetParameters(
                from_account=from_account,
                to_address=receiver,
                amount=amount,
                asset_id=asset,
            ),
        )
