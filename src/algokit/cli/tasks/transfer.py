import logging

import algosdk
import algosdk.encoding
import click
from algokit_utils import (
    Account,
    TransferAssetParameters,
    TransferParameters,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
    transfer_asset,
)

logger = logging.getLogger(__name__)

# TODO: upon algokit aliasing being merged sender will be expanded ot work with aliases
# TODO: upon algokit nfd lookup being implemented receiver will also allow nfd lookups


def _get_private_key_from_mnemonic() -> str:
    mnemonic_phrase = click.prompt("Enter the mnemonic phrase (25 words separated by whitespace)", hide_input=True)
    try:
        return str(algosdk.mnemonic.to_private_key(mnemonic_phrase))  # type: ignore[no-untyped-call]
    except Exception as err:
        raise click.ClickException("Invalid mnemonic. Please provide a valid Algorand mnemonic.") from err


def _get_algod_client(network: str) -> algosdk.v2client.algod.AlgodClient:
    network_mapping = {
        "localnet": get_algod_client(get_default_localnet_config("algod")),
        "testnet": get_algod_client(get_algonode_config("testnet", "algod", "")),
        "mainnet": get_algod_client(get_algonode_config("mainnet", "algod", "")),
    }
    try:
        return network_mapping[network]
    except KeyError as err:
        raise click.ClickException("Invalid network") from err


def _get_asset_decimals(asset_id: int, algod_client: algosdk.v2client.algod.AlgodClient) -> int:
    if asset_id == 0:
        return 6

    asset_info = algod_client.asset_info(asset_id)

    if not isinstance(asset_info, dict):
        raise click.ClickException("Invalid asset info response")

    return asset_info.get("decimals", 0)


def _validate_address(address: str) -> None:
    if not algosdk.encoding.is_valid_address(address):  # type: ignore[no-untyped-call]
        raise click.ClickException(f"{address} is an invalid account address")


def _validate_asset_balance(sender_account_info: dict, receiver_account_info: dict, asset_id: int, amount: int) -> None:
    sender_asset_record = next(
        (asset for asset in sender_account_info.get("assets", []) if asset["asset-id"] == asset_id), None
    )
    receiver_asset_record = next(
        (asset for asset in receiver_account_info.get("assets", []) if asset["asset-id"] == asset_id), None
    )
    if not sender_asset_record:
        raise click.ClickException("Sender is not opted into the asset")
    if sender_asset_record["amount"] < amount:
        raise click.ClickException("Insufficient asset balance in sender account")
    if not receiver_asset_record:
        raise click.ClickException("Receiver is not opted into the asset")


def _validate_balance(
    sender: str, receiver: str, asset_id: int, amount: int, algod_client: algosdk.v2client.algod.AlgodClient
) -> None:
    sender_account_info = algod_client.account_info(sender)
    receiver_account_info = algod_client.account_info(receiver)

    if not isinstance(sender_account_info, dict) or not isinstance(receiver_account_info, dict):
        raise click.ClickException("Invalid account info response")

    if asset_id == 0:
        if isinstance(sender_account_info, dict) and sender_account_info.get("amount", 0) < amount:
            raise click.ClickException("Insufficient Algos balance in sender account")
    else:
        _validate_asset_balance(sender_account_info, receiver_account_info, asset_id, amount)


def _validate_inputs(
    sender: str, receiver: str, asset_id: int, amount: int, algod_client: algosdk.v2client.algod.AlgodClient
) -> None:
    for address in [sender, receiver]:
        _validate_address(address)
    _validate_balance(sender, receiver, asset_id, amount, algod_client)


@click.command(name="transfer")
@click.option("--sender", "-s", type=click.STRING, help="Address of the sender account")
@click.option("--receiver", "-r", type=click.STRING, help="Address to an account that will receive the asset(s)")
@click.option("--asset", "--id", "asset_id", type=click.INT, help="ASA asset id to transfer", default=0)
@click.option("--amount", "-a", type=click.INT, help="Amount to transfer")
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
)
@click.option("--network", "-n", help="Network where the transfer will be executed localnet|testnet|mainnet")
def transfer(  # noqa: PLR0913
    *,
    sender: str,
    receiver: str,
    asset_id: int,
    amount: int,
    whole_units: bool,
    network: str,
) -> None:
    # Trim special characters from sender and receiver addresses
    sender = sender.strip('"')
    receiver = receiver.strip('"')

    # Get algod client
    algod_client = _get_algod_client(network)

    # Validate inputs
    _validate_inputs(sender, receiver, asset_id, amount, algod_client)

    # Convert amount to whole units if specified
    if whole_units:
        amount = amount * (10 ** _get_asset_decimals(asset_id, algod_client))

    # Assemble sender account
    private_key = _get_private_key_from_mnemonic()
    from_account = Account(address=sender, private_key=private_key)

    # Transfer algos or assets depending on asset_id
    if asset_id == 0:
        transfer(algod_client, TransferParameters(to_address=receiver, from_account=from_account, micro_algos=amount))
    else:
        transfer_asset(
            algod_client,
            TransferAssetParameters(
                from_account=from_account,
                to_address=receiver,
                amount=amount,
                asset_id=asset_id,
            ),
        )
