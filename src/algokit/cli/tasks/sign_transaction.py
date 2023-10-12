import base64
import json
import logging
from pathlib import Path
from typing import Any, cast

import click
from algosdk import encoding
from algosdk.transaction import SignedTransaction, Transaction, retrieve_from_file, write_to_file

from algokit.cli.common.utils import MutuallyExclusiveOption
from algokit.cli.tasks.utils import get_account_with_private_key

logger = logging.getLogger(__name__)


class TransactionBytesEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:  # noqa: ANN401
        if isinstance(obj, bytes | bytearray):
            return base64.b64encode(obj).decode()
        return super().default(obj)


def _validate_for_signed_txns(txns: list[Transaction]) -> None:
    signed_txns = [txn for txn in txns if isinstance(txn, SignedTransaction)]

    if signed_txns:
        transaction_ids = ", ".join([txn.get_txid() for txn in signed_txns])  # type: ignore[no-untyped-call]
        message = f"Supplied transactions {transaction_ids} are already signed!"
        raise click.ClickException(message)


def _get_transactions(file: Path | None, transaction: str | None) -> list[Transaction]:
    try:
        if file:
            txns: list[Transaction] = retrieve_from_file(str(file))  # type: ignore[no-untyped-call]
            return txns
        else:
            return [cast(Transaction, encoding.msgpack_decode(transaction))]  # type: ignore[no-untyped-call]
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
                    "transaction_id": txn.get_txid(),  # type: ignore[no-untyped-call]
                    "content": txn.dictify(),  # type: ignore[no-untyped-call]
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


def _sign_and_output_transaction(txns: list[Transaction], private_key: str, output: Path | None) -> None:
    signed_txns = [txn.sign(private_key) for txn in txns]  # type: ignore[no-untyped-call]

    if output:
        write_to_file(signed_txns, str(output))  # type: ignore[no-untyped-call]
        click.echo(f"Signed transaction written to {output}")
    else:
        encoded_signed_txns = [
            {"transaction_id": txn.get_txid(), "content": encoding.msgpack_encode(txn)}  # type: ignore[no-untyped-call]
            for txn in signed_txns
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

    _sign_and_output_transaction(txns, signer_account.private_key, output)
