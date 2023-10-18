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
from algosdk.util import microalgos_to_algos

from algokit.core.tasks.wallet import get_alias

logger = logging.getLogger(__name__)


def _validate_asset_balance(account_info: dict, asset_id: int, decimals: int, amount: int = 0) -> None:
    asset_record = next((asset for asset in account_info.get("assets", []) if asset["asset-id"] == asset_id), None)

    if not asset_record:
        raise click.ClickException("Account is not opted into the asset")

    if amount > 0 and asset_record["amount"] < amount:
        required = amount / 10**decimals
        available = asset_record["amount"] / 10**decimals
        raise click.ClickException(
            f"Insufficient asset balance in account, required: {required}, available: {available}"
        )


def _validate_algo_balance(account_info: dict, amount: int) -> None:
    if account_info.get("amount", 0) < amount:
        required = microalgos_to_algos(amount)  # type: ignore[no-untyped-call]
        available = microalgos_to_algos(account_info.get("amount", 0))  # type: ignore[no-untyped-call]
        raise click.ClickException(
            f"Insufficient Algos balance in account, required: {required} Algos, available: {available} Algos"
        )


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
    algod_client: algosdk.v2client.algod.AlgodClient, account: Account | str, asset_id: int, amount: int = 0
) -> None:
    """
    Validates the balance of an account before an operation.

    Args:
        algod_client (algosdk.v2client.algod.AlgodClient): The AlgodClient object for
        interacting with the Algorand blockchain.
        account (Account | str): The account object.
        asset_id (int): The ID of the asset to be checked (0 for Algos).
        amount (int): The amount of Algos or asset for the operation. Defaults to 0 implying opt-in check only.

    Raises:
        click.ClickException: If any validation check fails.
    """
    address = account.address if isinstance(account, Account) else account
    account_info = algod_client.account_info(address)

    if not isinstance(account_info, dict):
        raise click.ClickException("Invalid account info response")

    if asset_id == 0:
        _validate_algo_balance(account_info, amount)
    else:
        decimals = get_asset_decimals(asset_id, algod_client)
        _validate_asset_balance(account_info, asset_id, decimals, amount)


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


def get_transaction_explorer_url(transaction_id: str, network: str) -> str:
    """
    Returns a URL for exploring a transaction on the specified network.

    Args:
        transaction_id (str): The ID of the transaction.
        network (str): The name of the network (e.g., "localnet", "testnet", "mainnet").

    Returns:
        str: The URL for exploring the transaction on the specified network.

    Raises:
        ValueError: If the network is invalid.
    """
    if network == "localnet":
        return f"https://app.dappflow.org/setnetwork?name=sandbox&redirect=explorer/transaction/{transaction_id}/"
    elif network == "testnet":
        return f"https://testnet.algoexplorer.io/tx/{transaction_id}"
    elif network == "mainnet":
        return f"https://algoexplorer.io/tx/{transaction_id}"
    else:
        raise ValueError(f"Invalid network: {network}")


def get_asset_explorer_url(asset_id: int, network: str) -> str:
    """
    Returns a URL for exploring a asset on the specified network.

    Args:
        asset_id (int): The ID of the asset.
        network (str): The name of the network (e.g., "localnet", "testnet", "mainnet").

    Returns:
        str: The URL for exploring the asset on the specified network.

    Raises:
        ValueError: If the network is invalid.
    """
    if network == "localnet":
        return f"https://app.dappflow.org/setnetwork?name=sandbox&redirect=explorer/asset/{asset_id}/"
    elif network == "testnet":
        return f"https://testnet.explorer.perawallet.app/assets/{asset_id}"
    elif network == "mainnet":
        return f"https://explorer.perawallet.app/assets/{asset_id}"
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
