import logging
import os
import stat
import sys

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


def get_private_key_from_mnemonic() -> str:
    """
    Converts a mnemonic phrase into a private key.

    Returns:
        str: The private key generated from the mnemonic phrase.

    Raises:
        click.ClickException: If the entered mnemonic phrase is invalid.

    Example Usage:
        private_key = get_private_key_from_mnemonic()
        print(private_key)

    Inputs:
        None

    Flow:
        1. Prompts the user to enter a mnemonic phrase.
        2. Converts the entered mnemonic phrase into a private key using `algosdk.mnemonic.to_private_key`.
        3. Returns the private key.

    """

    mnemonic_phrase = click.prompt("Enter the mnemonic phrase (25 words separated by whitespace)", hide_input=True)
    try:
        return str(algosdk.mnemonic.to_private_key(mnemonic_phrase))  # type: ignore[no-untyped-call]
    except Exception as err:
        raise click.ClickException("Invalid mnemonic. Please provide a valid Algorand mnemonic.") from err


def load_algod_client(network: str) -> algosdk.v2client.algod.AlgodClient:
    """
    Returns an instance of the `algosdk.v2client.algod.AlgodClient` class for the specified network.

    Args:
        network (str): The network for which the `AlgodClient` instance needs to be loaded.

    Returns:
        algosdk.v2client.algod.AlgodClient: An instance of the `AlgodClient` class for the specified network.

    Raises:
        click.ClickException: If the specified network is invalid.
    """

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
    """
    Retrieves the number of decimal places for a given asset.

    Args:
        asset_id (int): The ID of the asset for which the number of decimal places is to be retrieved. (0 for Algo)
        algod_client (algosdk.v2client.algod.AlgodClient): An instance of the AlgodClient class.

    Returns:
        int: The number of decimal places for the given asset.

    Raises:
        click.ClickException: If the asset info response is invalid.

    Example:
        asset_id = 123
        algod_client = algosdk.v2client.algod.AlgodClient("https://api.algoexplorer.io", "API_KEY")
        decimals = get_asset_decimals(asset_id, algod_client)
        print(decimals)
    """

    if asset_id == 0:
        return 6

    asset_info = algod_client.asset_info(asset_id)

    if not isinstance(asset_info, dict) or "params" not in asset_info or "decimals" not in asset_info["params"]:
        raise click.ClickException("Invalid asset info response")

    return int(asset_info["params"]["decimals"])


def validate_balance(
    sender: Account, receiver: str, asset_id: int, amount: int, algod_client: algosdk.v2client.algod.AlgodClient
) -> None:
    """
    Validates the balance of a sender's account before transferring assets or Algos to a receiver's account.

    Args:
        sender (Account): The sender's account object.
        receiver (str): The receiver's account address.
        asset_id (int): The ID of the asset to be transferred (0 for Algos).
        amount (int): The amount of Algos or asset to be transferred.
        algod_client (algosdk.v2client.algod.AlgodClient): The AlgodClient object for
        interacting with the Algorand blockchain.

    Raises:
        click.ClickException: If any validation check fails.
    """

    sender_account_info = algod_client.account_info(sender.address)
    receiver_account_info = algod_client.account_info(receiver)

    if not isinstance(sender_account_info, dict) or not isinstance(receiver_account_info, dict):
        raise click.ClickException("Invalid account info response")

    if asset_id == 0:
        _validate_algo_balance(sender_account_info, amount)
    else:
        _validate_asset_balance(sender_account_info, receiver_account_info, asset_id, amount)


def validate_address(address: str) -> None:
    """
    Check if a given address is a valid Algorand account address.

    Args:
        address (str): The address to be validated.

    Raises:
        click.ClickException: If the address is invalid.

    Returns:
        None
    """

    if not algosdk.encoding.is_valid_address(address):  # type: ignore[no-untyped-call]
        raise click.ClickException(f"`{address}` is an invalid account address")


def get_account_with_private_key(address: str) -> Account:
    """
    Retrieves an account object with the private key based on the provided address.

    Args:
        address (str): The address for which to retrieve the account object.

    Returns:
        Account: An account object with the address and private key.

    Raises:
        click.ClickException: If the address is not valid or if the alias does not exist or does not have a private key.
    """

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
    """
    Validates the given address and returns it if valid. If the address is not valid,
    it checks if the address is an alias and returns the corresponding address if the alias exists.

    Args:
        address (str): The address to be validated or checked for an alias.

    Returns:
        str: The validated address or the corresponding address from an alias.

    Raises:
        click.ClickException: If the address is not valid and no corresponding alias exists.

    Example:
        address = get_address("ABCD1234")
        print(address)
    """

    parsed_address = address.strip('"')

    try:
        validate_address(parsed_address)
        return parsed_address
    except click.ClickException as ex:
        if len(parsed_address) == algosdk.constants.address_len:
            raise click.ClickException(f"`{parsed_address}` is an invalid account address") from ex

        alias_data = get_alias(parsed_address)

        if not alias_data:
            raise click.ClickException(f"Alias `{parsed_address}` alias does not exist.") from ex

        return alias_data.address


def get_transaction_explorer_url(txn_id: str, network: str) -> str:
    """
    Returns a URL for exploring a transaction on the specified network.

    Args:
        txn_id (str): The ID of the transaction.
        network (str): The name of the network (e.g., "localnet", "testnet", "mainnet").

    Returns:
        str: The URL for exploring the transaction on the specified network.

    Raises:
        ValueError: If the network is invalid.
    """
    if network == "localnet":
        return f"https://app.dappflow.org/setnetwork?name=sandbox&redirect=explorer/transaction/{txn_id}/"
    elif network == "testnet":
        return f"https://testnet.algoexplorer.io/tx/{txn_id}"
    elif network == "mainnet":
        return f"https://algoexplorer.io/tx/{txn_id}"
    else:
        raise ValueError(f"Invalid network: {network}")


def stdin_has_content() -> bool:
    """
    Checks if there is content in the standard input.

    Returns:
        bool: True if there is content in the standard input, False otherwise.
    """

    mode = os.fstat(sys.stdin.fileno()).st_mode
    return stat.S_ISFIFO(mode) or stat.S_ISREG(mode)
