import base64
import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import click
import msgpack
from algokit_utils.transact import (
    SignedTransaction,
    Transaction,
    decode_signed_transaction,
    decode_transaction,
    encode_signed_transactions,
    get_transaction_id,
    to_transaction_dto,
)

from algokit.cli.common.utils import MutuallyExclusiveOption
from algokit.cli.tasks.utils import get_account_with_private_key
from algokit.core.signing_account import SigningAccount

logger = logging.getLogger(__name__)


class TransactionBytesEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:  # noqa: ANN401
        if isinstance(obj, bytes | bytearray):
            return base64.b64encode(obj).decode()
        return super().default(obj)


def retrieve_from_file(file_path: str) -> list[Transaction | SignedTransaction]:
    """Load transactions from a file (msgpack encoded).

    The file format is concatenated msgpack-encoded transactions, each prefixed with "TX".
    Each transaction can be either a Transaction or a SignedTransaction.

    Args:
        file_path: Path to the file containing encoded transactions.

    Returns:
        List of Transaction or SignedTransaction objects.
    """
    with Path(file_path).open("rb") as f:
        data = f.read()

    tx_prefix = b"TX"
    txns: list[Transaction | SignedTransaction] = []
    offset = 0

    while offset < len(data):
        # Check for TX prefix and skip it if present
        has_prefix = data[offset:].startswith(tx_prefix)
        if has_prefix:
            msgpack_start = offset + len(tx_prefix)
        else:
            msgpack_start = offset

        # Use Unpacker to find the end of the msgpack object
        unpacker = msgpack.Unpacker(raw=True, strict_map_key=False)
        unpacker.feed(data[msgpack_start:])
        try:
            _ = unpacker.unpack()  # Just to advance the position
            msgpack_bytes_consumed = unpacker.tell()

            # Include the prefix in the encoded transaction if present
            if has_prefix:
                encoded_txn = data[offset : msgpack_start + msgpack_bytes_consumed]
            else:
                encoded_txn = data[offset : offset + msgpack_bytes_consumed]
            offset = msgpack_start + msgpack_bytes_consumed

            # Try to decode as SignedTransaction first, then Transaction
            try:
                txns.append(decode_signed_transaction(encoded_txn))
            except Exception:
                txns.append(decode_transaction(encoded_txn))
        except msgpack.OutOfData:
            break

    return txns


def write_to_file(signed_txns: list[SignedTransaction], file_path: str) -> None:
    """Write signed transactions to a file (msgpack encoded).

    The file format is concatenated msgpack-encoded signed transactions.

    Args:
        signed_txns: List of SignedTransaction objects to write.
        file_path: Path to the output file.
    """
    # Encode each signed transaction
    encoded_txns = encode_signed_transactions(signed_txns)

    # Write concatenated msgpack objects (not an array)
    with Path(file_path).open("wb") as f:
        for encoded_txn in encoded_txns:
            f.write(encoded_txn)


def _validate_for_signed_txns(txns: Sequence[Transaction | SignedTransaction]) -> None:
    signed_txns = [txn for txn in txns if isinstance(txn, SignedTransaction)]

    if signed_txns:
        transaction_ids = ", ".join([get_transaction_id(txn.txn) for txn in signed_txns])
        message = f"Supplied transactions {transaction_ids} are already signed!"
        raise click.ClickException(message)


def _get_transactions(file: Path | None, transaction: str | None) -> list[Transaction]:
    try:
        if file:
            txns_or_signed = retrieve_from_file(str(file))
            # Extract unsigned transactions, filter out any that are already signed
            return [txn if isinstance(txn, Transaction) else txn.txn for txn in txns_or_signed]
        else:
            # Decode base64 string to bytes, then decode as transaction
            assert transaction is not None, "Either file or transaction must be provided"
            txn_bytes = base64.b64decode(transaction)
            return [decode_transaction(txn_bytes)]
    except Exception as ex:
        logger.debug(ex, exc_info=True)
        raise click.ClickException(
            "Failed to decode transaction! If you are intending to sign multiple transactions use `--file` instead."
        ) from ex


def _confirm_transaction(txns: list[Transaction]) -> bool:
    click.echo(
        json.dumps(
            [
                {
                    "transaction_id": get_transaction_id(txn),
                    "content": to_transaction_dto(txn),
                }
                for txn in txns
            ],
            cls=TransactionBytesEncoder,
            indent=2,
        ),
    )
    response = click.prompt(
        "Would you like to proceed with signing the above?", type=click.Choice(["y", "n"]), default="n"
    )
    return bool(response == "y")


def _sign_and_output_transaction(txns: list[Transaction], signing_account: SigningAccount, output: Path | None) -> None:
    # Create a transaction signer from the private key

    # Sign all transactions - signer returns encoded SignedTransaction bytes
    signed_txn_bytes_list = signing_account.signer(txns, list(range(len(txns))))

    # Decode the signed transaction bytes to get SignedTransaction objects
    signed_txns = [decode_signed_transaction(stx_bytes) for stx_bytes in signed_txn_bytes_list]

    if output:
        write_to_file(signed_txns, str(output))
        click.echo(f"Signed transaction written to {output}")
    else:
        encoded_signed_txns = [
            {
                "transaction_id": get_transaction_id(txn.txn),
                "content": base64.b64encode(stx_bytes).decode(),
            }
            for txn, stx_bytes in zip(signed_txns, signed_txn_bytes_list, strict=False)
        ]
        click.echo(json.dumps(encoded_signed_txns, indent=2))


@click.command(name="sign", help="Sign goal clerk compatible Algorand transaction(s).")
@click.option("--account", "-a", type=click.STRING, required=True, help="Address or alias of the signer account.")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    help="Single or multiple message pack encoded transactions from binary file to sign.",
    cls=MutuallyExclusiveOption,
    not_required_if=["transaction"],
)
@click.option(
    "--transaction",
    "-t",
    type=click.STRING,
    help="Single base64 encoded transaction object to sign.",
    cls=MutuallyExclusiveOption,
    not_required_if=["file"],
)
@click.option(
    "--output",
    "-o",
    type=click.Path(resolve_path=True, dir_okay=False, file_okay=True, path_type=Path),
    help="The output file path to store signed transaction(s).",
    required=False,
)
@click.option("--force", is_flag=True, help="Force signing without confirmation.", required=False, type=click.BOOL)
def sign(*, account: str, file: Path | None, transaction: str | None, output: Path | None, force: bool) -> None:
    if not file and not transaction:
        raise click.ClickException(
            "Please provide a file path via `--file` or a base64 encoded unsigned transaction via `--transaction`."
        )

    signer_account = get_account_with_private_key(account)

    txns = _get_transactions(file, transaction)

    if not txns:
        raise click.ClickException("No valid transactions found!")

    _validate_for_signed_txns(txns)

    if not force and not _confirm_transaction(txns):
        return

    _sign_and_output_transaction(txns, signer_account, output)
