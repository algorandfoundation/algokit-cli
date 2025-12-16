import base64
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, cast

import click
import msgpack
from algokit_utils.clients import UnexpectedStatusError
from algokit_utils.transact import SignedTransaction, decode_signed_transaction, encode_signed_transaction

from algokit.cli.common.constants import AlgorandNetwork, ExplorerEntityType
from algokit.cli.common.utils import MutuallyExclusiveOption, get_explorer_url
from algokit.cli.tasks.utils import (
    load_algod_client,
    stdin_has_content,
)

if TYPE_CHECKING:
    from io import TextIOWrapper

logger = logging.getLogger(__name__)


def _is_sign_task_output_txn(item: dict) -> bool:
    """
    Checks if a given item is a dictionary and contains the keys "transaction_id" and "content".

    Args:
        item (dict): A dictionary object to be checked.

    Returns:
        bool: True if the input item is a dictionary with the keys "transaction_id" and "content", False otherwise.
    """

    return isinstance(item, dict) and all(key in item for key in ["transaction_id", "content"])


def _retrieve_transactions_from_file(file_path: Path) -> list[SignedTransaction]:
    """
    Load signed transactions from a file containing msgpack-encoded data.

    Args:
        file_path: Path to the file containing signed transaction(s)

    Returns:
        A list of SignedTransaction objects

    Raises:
        click.ClickException: If the file cannot be read or decoded
    """
    try:
        file_content = file_path.read_bytes()

        # Try to decode as a single transaction first
        try:
            return [decode_signed_transaction(file_content)]
        except Exception:
            pass

        # Try to parse multiple concatenated msgpack objects
        transactions: list[SignedTransaction] = []
        offset = 0

        while offset < len(file_content):
            # Use msgpack Unpacker to find the boundaries of each msgpack object
            unpacker = msgpack.Unpacker(raw=True, strict_map_key=False)
            unpacker.feed(file_content[offset:])
            try:
                _ = unpacker.unpack()  # Advance to get the position
                msgpack_bytes_consumed = unpacker.tell()

                # Extract just this msgpack object
                encoded_txn = file_content[offset : offset + msgpack_bytes_consumed]
                offset += msgpack_bytes_consumed

                # Decode the signed transaction
                stx = decode_signed_transaction(encoded_txn)
                transactions.append(stx)
            except msgpack.OutOfData:
                break
            except Exception:
                break

        if transactions:
            return transactions
        raise ValueError("No valid transactions found in file") from None
    except Exception as ex:
        logger.debug(ex, exc_info=True)
        raise click.ClickException(f"Failed to read transactions from file: {ex}") from ex


def _load_from_stdin() -> list[SignedTransaction]:
    """
    Load transaction data from standard input and convert it into a list of SignedTransaction objects.

    Returns:
        A list of SignedTransaction objects representing the loaded transactions from the standard input.

    Raises:
        click.ClickException: If the piped transaction content is invalid.
    """
    # Read the raw file content from the standard input

    raw_file_content = cast("TextIOWrapper", click.get_text_stream("stdin")).read()

    try:
        # Parse the raw file content as JSON
        file_content = json.loads(raw_file_content)
    except json.JSONDecodeError as ex:
        raise click.ClickException("Invalid piped transaction content!") from ex

    # Check if the content is a list of dicts with the required fields
    if not isinstance(file_content, list) or not all(_is_sign_task_output_txn(item) for item in file_content):
        raise click.ClickException("Invalid piped transaction content!")

    # Convert the content into SignedTransaction objects
    return [decode_signed_transaction(base64.b64decode(item["content"])) for item in file_content]


def _get_signed_transactions(file: Path | None = None, transaction: str | None = None) -> list[SignedTransaction]:
    """
    Retrieves a list of signed transactions.

    Args:
        file (Optional[Path]): A `Path` object representing the file path from which to retrieve the transactions.
        transaction (Optional[str]): A base64 encoded string representing a single signed transaction.

    Returns:
        list[SignedTransaction]: A list of `SignedTransaction` objects representing the retrieved signed transactions.

    Raises:
        click.ClickException: If the supplied transaction is not of type `SignedTransaction`.
        click.ClickException: If there is an error decoding the transaction.

    """
    try:
        if file:
            txns = _retrieve_transactions_from_file(file)
        elif transaction:
            txns = [decode_signed_transaction(base64.b64decode(transaction))]
        else:
            txns = _load_from_stdin()

        for txn in txns:
            if not isinstance(txn, SignedTransaction):
                raise click.ClickException("Supplied transaction is not signed!")

        return txns

    except Exception as ex:
        logger.debug(ex, exc_info=True)
        raise click.ClickException(
            "Failed to decode transaction! If you are intending to send multiple transactions use `--file` instead."
        ) from ex


def _send_transactions(network: AlgorandNetwork, txns: list[SignedTransaction]) -> None:
    """
    Sends a list of signed transactions to the Algorand blockchain network using the AlgodClient.

    Args:
        network (AlgorandNetwork): The network to which the transactions will be sent.
        txns (list[SignedTransaction]): A list of signed transactions to be sent.

    Returns:
        None: The function does not return any value.
    """
    algod_client = load_algod_client(network)

    if any(txn.txn.group for txn in txns):
        # Send all transactions as a group
        encoded_txns = [encode_signed_transaction(txn) for txn in txns]
        result = algod_client.send_raw_transaction(encoded_txns)
        txid = result.tx_id
        click.echo(f"Transaction group successfully sent with txid: {txid}")
        click.echo(
            f"Check transaction group status at: {get_explorer_url(txid, network, ExplorerEntityType.TRANSACTION)}"
        )
    else:
        for index, txn in enumerate(txns, start=1):
            click.echo(f"\nSending transaction {index}/{len(txns)}")
            encoded_txn = encode_signed_transaction(txn)
            result = algod_client.send_raw_transaction(encoded_txn)
            txid = result.tx_id
            click.echo(f"Transaction successfully sent with txid: {txid}")
            click.echo(
                f"Check transaction status at: {get_explorer_url(txid, network, ExplorerEntityType.TRANSACTION)}"
            )


@click.command(name="send", help="Send a signed transaction to the given network.")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    help="Single or multiple message pack encoded signed transactions from binary file to send.",
    cls=MutuallyExclusiveOption,
    not_required_if=["transaction"],
    required=False,
)
@click.option(
    "--transaction",
    "-t",
    type=click.STRING,
    help="Base64 encoded signed transaction to send.",
    cls=MutuallyExclusiveOption,
    not_required_if=["file"],
    required=False,
)
@click.option(
    "-n",
    "--network",
    type=click.Choice(AlgorandNetwork.to_list()),
    default=AlgorandNetwork.LOCALNET,
    required=False,
    help=f"Network to use. Refers to `{AlgorandNetwork.LOCALNET}` by default.",
)
def send(*, file: Path | None, transaction: str | None, network: AlgorandNetwork) -> None:
    if not file and not transaction and not stdin_has_content():
        raise click.ClickException(
            "Please provide a file path via `--file` or a base64 encoded signed transaction via `--transaction`. "
            "Alternatively, you can also pipe the output of `algokit task sign` to this command."
        )

    txns = _get_signed_transactions(file, transaction)

    if not txns:
        raise click.ClickException("No valid transactions found!")

    try:
        _send_transactions(network, txns)
    except UnexpectedStatusError as ex:
        raise click.ClickException(str(ex)) from ex
    except Exception as ex:
        logger.debug(ex, exc_info=True)
        raise click.ClickException("Failed to send transaction!") from ex
