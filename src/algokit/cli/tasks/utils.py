import logging

import algosdk
import algosdk.encoding
import click
from algokit_utils import (
    Account,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
)

from algokit.core.tasks.wallet import get_alias

logger = logging.getLogger(__name__)


def get_private_key_from_mnemonic() -> str:
    mnemonic_phrase = click.prompt("Enter the mnemonic phrase (25 words separated by whitespace)", hide_input=True)
    try:
        return str(algosdk.mnemonic.to_private_key(mnemonic_phrase))  # type: ignore[no-untyped-call]
    except Exception as err:
        raise click.ClickException("Invalid mnemonic. Please provide a valid Algorand mnemonic.") from err


def load_algod_client(network: str) -> algosdk.v2client.algod.AlgodClient:
    config_mapping = {
        "localnet": get_default_localnet_config("algod"),
        "testnet": get_algonode_config("testnet", "algod", ""),
        "mainnet": get_algonode_config("mainnet", "algod", ""),
    }
    try:
        return get_algod_client(config_mapping[network])
    except KeyError as err:
        raise click.ClickException("Invalid network") from err


def get_asset_decimals(asset_id: int, algod_client: algosdk.v2client.algod.AlgodClient) -> int:
    if asset_id == 0:
        return 6

    asset_info = algod_client.asset_info(asset_id)

    if not isinstance(asset_info, dict) or "params" not in asset_info or "decimals" not in asset_info["params"]:
        raise click.ClickException("Invalid asset info response")

    return int(asset_info["params"]["decimals"])


def validate_address(address: str) -> None:
    if not algosdk.encoding.is_valid_address(address):  # type: ignore[no-untyped-call]
        raise click.ClickException(f"{address} is an invalid account address")


def validate_asset_balance(sender_account_info: dict, receiver_account_info: dict, asset_id: int, amount: int) -> None:
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


def validate_algo_balance(sender_account_info: dict, amount: int) -> None:
    if sender_account_info.get("amount", 0) < amount:
        raise click.ClickException("Insufficient Algos balance in sender account")


def validate_balance(
    sender: Account, receiver: str, asset_id: int, amount: int, algod_client: algosdk.v2client.algod.AlgodClient
) -> None:
    sender_account_info = algod_client.account_info(sender.address)
    receiver_account_info = algod_client.account_info(receiver)

    if not isinstance(sender_account_info, dict) or not isinstance(receiver_account_info, dict):
        raise click.ClickException("Invalid account info response")

    if asset_id == 0:
        validate_algo_balance(sender_account_info, amount)
    else:
        validate_asset_balance(sender_account_info, receiver_account_info, asset_id, amount)


def get_account_with_private_key(address: str) -> Account:
    parsed_address = address.strip('"')

    try:
        validate_address(parsed_address)
        pk = get_private_key_from_mnemonic()
        return Account(address=parsed_address, private_key=pk)
    except click.ClickException as ex:
        alias_data = get_alias(parsed_address)

        if not alias_data:
            raise click.ClickException(f"Alias `{parsed_address}` alias does not exist.") from ex
        if not alias_data.private_key:
            raise click.ClickException(f"Alias `{parsed_address}` does not have a private key.") from ex

        return Account(address=alias_data.address, private_key=alias_data.private_key)


def get_address(address: str) -> str:
    parsed_address = address.strip('"')

    try:
        validate_address(parsed_address)
        return parsed_address
    except click.ClickException as ex:
        alias_data = get_alias(parsed_address)

        if not alias_data:
            raise click.ClickException(f"Alias `{parsed_address}` alias does not exist.") from ex

        return alias_data.address
