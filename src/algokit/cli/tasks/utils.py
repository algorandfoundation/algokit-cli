# AlgoKit Tasks related utility functions

import logging
import os
import stat
import sys
from collections.abc import Callable
from functools import wraps
from typing import Any

import algosdk
import algosdk.encoding
import click
from algokit_utils import (
    Account,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
)
from algosdk.util import algos_to_microalgos, microalgos_to_algos

from algokit.cli.common.constants import AlgorandNetwork
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


def load_algod_client(network: AlgorandNetwork) -> algosdk.v2client.algod.AlgodClient:
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
        AlgorandNetwork.LOCALNET: get_default_localnet_config("algod"),
        AlgorandNetwork.TESTNET: get_algonode_config("testnet", "algod", ""),
        AlgorandNetwork.MAINNET: get_algonode_config("mainnet", "algod", ""),
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
        algod_client = algosdk.v2client.algod.AlgodClient("https://mainnet-api.algonode.cloud", "API_KEY")
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


def stdin_has_content() -> bool:
    """
    Checks if there is content in the standard input.

    Returns:
        bool: True if there is content in the standard input, False otherwise.
    """

    mode = os.fstat(sys.stdin.fileno()).st_mode
    return stat.S_ISFIFO(mode) or stat.S_ISREG(mode)


def validate_account_balance_to_opt_in(
    algod_client: algosdk.v2client.algod.AlgodClient, account: Account, num_assets: int
) -> None:
    """
    Validates the balance of an account before opt in operation.
    Each asset requires 0.1 Algos to opt in.

    Args:
        algod_client (algosdk.v2client.algod.AlgodClient): The AlgodClient object for
        interacting with the Algorand blockchain.
        account (Account | str): The account object.
        num_assets (int): The number of the assets for opt in (0 for Algos).

    Raises:
        click.ClickException: If there is an insufficient fund in the account or account is not valid.
    """

    address = account.address if isinstance(account, Account) else account
    account_info = algod_client.account_info(address)

    if not isinstance(account_info, dict):
        raise click.ClickException("Invalid account info response")

    required_microalgos = num_assets * algos_to_microalgos(0.1)  # type: ignore[no-untyped-call]
    available_microalgos = account_info.get("amount", 0)
    if available_microalgos < required_microalgos:
        required_algo = microalgos_to_algos(required_microalgos)  # type: ignore[no-untyped-call]
        available_algos = microalgos_to_algos(available_microalgos)  # type: ignore[no-untyped-call]
        raise click.ClickException(
            f"Insufficient Algos balance in account to opt in, required: {required_algo} Algos, available:"
            f" {available_algos} Algos"
        )


def get_account_info(algod_client: algosdk.v2client.algod.AlgodClient, account_address: str) -> dict:
    account_info = algod_client.account_info(account_address)
    assert isinstance(account_info, dict)
    return account_info


def run_callback_once(callback: Callable) -> Callable:
    """
    Click option callbacks run twice, first to validate the prompt input,
    and then independently from that is used to validate the value passed to the option.

    In cases where the callback is expensive or has side effects(like prompting the user),
    it's better to run it only once.
    """

    @wraps(callback)
    def wrapper(context: click.Context, param: click.Parameter, value: Any) -> Any:  # noqa: ANN401
        if context.obj is None:
            context.obj = {}

        key = f"{param.name}_callback_result"
        if key not in context.obj:
            result = callback(context, param, value)
            context.obj[key] = result
            return result
        return context.obj[key]

    return wrapper
