import logging
from typing import TYPE_CHECKING

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
from algokit_utils import (
    transfer as transfer_algos,
)

from algokit.core.tasks.wallet import get_alias

if TYPE_CHECKING:
    from algosdk.transaction import AssetTransferTxn, PaymentTxn

logger = logging.getLogger(__name__)

# TODO: upon algokit nfd lookup being implemented receiver will also allow nfd lookups


def _get_private_key_from_mnemonic() -> str:
    mnemonic_phrase = click.prompt("Enter the mnemonic phrase (25 words separated by whitespace)", hide_input=True)
    try:
        return str(algosdk.mnemonic.to_private_key(mnemonic_phrase))  # type: ignore[no-untyped-call]
    except Exception as err:
        raise click.ClickException("Invalid mnemonic. Please provide a valid Algorand mnemonic.") from err


def _get_algod_client(network: str) -> algosdk.v2client.algod.AlgodClient:
    config_mapping = {
        "localnet": get_default_localnet_config("algod"),
        "testnet": get_algonode_config("testnet", "algod", ""),
        "mainnet": get_algonode_config("mainnet", "algod", ""),
    }
    try:
        return get_algod_client(config_mapping[network])
    except KeyError as err:
        raise click.ClickException("Invalid network") from err


def _get_asset_decimals(asset_id: int, algod_client: algosdk.v2client.algod.AlgodClient) -> int:
    if asset_id == 0:
        return 6

    asset_info = algod_client.asset_info(asset_id)

    if not isinstance(asset_info, dict) or "params" not in asset_info or "decimals" not in asset_info["params"]:
        raise click.ClickException("Invalid asset info response")

    return int(asset_info["params"]["decimals"])


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


def _validate_algo_balance(sender_account_info: dict, amount: int) -> None:
    if sender_account_info.get("amount", 0) < amount:
        raise click.ClickException("Insufficient Algos balance in sender account")


def _validate_balance(
    sender: Account, receiver: str, asset_id: int, amount: int, algod_client: algosdk.v2client.algod.AlgodClient
) -> None:
    sender_account_info = algod_client.account_info(sender.address)
    receiver_account_info = algod_client.account_info(receiver)

    if not isinstance(sender_account_info, dict) or not isinstance(receiver_account_info, dict):
        raise click.ClickException("Invalid account info response")

    if asset_id == 0:
        _validate_algo_balance(sender_account_info, amount)
    else:
        _validate_asset_balance(sender_account_info, receiver_account_info, asset_id, amount)


def _validate_inputs(
    sender: Account, receiver: str, asset_id: int, amount: int, algod_client: algosdk.v2client.algod.AlgodClient
) -> None:
    _validate_address(receiver)
    _validate_balance(sender, receiver, asset_id, amount, algod_client)


def _get_account_with_private_key(address: str) -> Account:
    parsed_address = address.strip('"')

    try:
        _validate_address(parsed_address)
        pk = _get_private_key_from_mnemonic()
        return Account(address=parsed_address, private_key=pk)
    except click.ClickException as ex:
        alias_data = get_alias(parsed_address)

        if not alias_data:
            raise click.ClickException(f"Alias `{parsed_address}` alias does not exist.") from ex
        if not alias_data.private_key:
            raise click.ClickException(f"Alias `{parsed_address}` does not have a private key.") from ex

        return Account(address=alias_data.address, private_key=alias_data.private_key)


def _get_address(address: str) -> str:
    parsed_address = address.strip('"')

    try:
        _validate_address(parsed_address)
        return parsed_address
    except click.ClickException as ex:
        alias_data = get_alias(parsed_address)

        if not alias_data:
            raise click.ClickException(f"Alias `{parsed_address}` alias does not exist.") from ex

        return alias_data.address


@click.command(name="transfer", help="""Transfer algos or assets from one account to another.""")
@click.option("--sender", "-s", type=click.STRING, help="Address or alias of the sender account", required=True)
@click.option(
    "--receiver",
    "-r",
    type=click.STRING,
    help="Address or alias to an account that will receive the asset(s)",
    required=True,
)
@click.option("--asset", "--id", "asset_id", type=click.INT, help="ASA asset id to transfer", default=0, required=False)
@click.option("--amount", "-a", type=click.INT, help="Amount to transfer", required=True)
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
    type=click.Choice(["localnet", "testnet", "mainnet"]),
    default="localnet",
    required=False,
    help="Network to use. Refers to `localnet` by default.",
)
def transfer(  # noqa: PLR0913
    *,
    sender: str,
    receiver: str,
    asset_id: int,
    amount: int,
    whole_units: bool,
    network: str,
) -> None:
    # Load addresses and accounts from mnemonics or aliases
    sender_account = _get_account_with_private_key(sender)
    receiver_address = _get_address(receiver)

    # Get algod client
    algod_client = _get_algod_client(network)

    # Convert amount to whole units if specified
    if whole_units:
        amount = amount * (10 ** _get_asset_decimals(asset_id, algod_client))

    # Validate inputs
    _validate_inputs(sender_account, receiver_address, asset_id, amount, algod_client)

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

        click.echo(
            f"Successfully performed transfer. "
            "See details at "
            f"https://testnet.algoexplorer.io/tx/{txn_response.get_txid()}"  # type: ignore[no-untyped-call]
        )

    except Exception as err:
        logger.debug(err, exc_info=True)
        raise click.ClickException("Failed to perform transfer") from err
