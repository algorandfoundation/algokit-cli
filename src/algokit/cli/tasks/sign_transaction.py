import json
from pathlib import Path
from typing import cast

import click
from algosdk import encoding
from algosdk.transaction import Transaction, retrieve_from_file, write_to_file

from algokit.cli.tasks.utils import get_account_with_private_key


def get_transaction(file: Path | None, transaction: str | None) -> Transaction:
    if file:
        txns: list[Transaction] = retrieve_from_file(str(file))  # type: ignore[no-untyped-call]
        if len(txns) > 1:
            raise click.ClickException("Only one transaction per file is supported.")
        return txns[0]
    elif transaction:
        return cast(Transaction, encoding.msgpack_decode(transaction))  # type: ignore[no-untyped-call]
    else:
        raise click.ClickException("Provide either a file to sign or a transaction to sign, not both or none.")


def confirm_transaction(txn: Transaction) -> bool:
    click.echo(json.dumps(txn.__dict__, indent=2))
    response = click.prompt("Do you want to sign the above transaction?", type=click.Choice(["y", "n"]), default="n")
    return bool(response == "y")


def sign_and_output_transaction(txn: Transaction, private_key: str, output: Path | None) -> None:
    signed_txn = txn.sign(private_key)  # type: ignore[no-untyped-call]

    if output:
        write_to_file([signed_txn], str(output))  # type: ignore[no-untyped-call]
        click.echo(f"Signed transaction written to {output}")
    else:
        click.echo(encoding.msgpack_encode({"txn": signed_txn.dictify()}))  # type: ignore[no-untyped-call]


@click.command(name="sign", help="Sign an Algorand transaction.")
@click.option("--account", "-a", type=str, required=True, help="The account alias.")
@click.option(
    "--file",
    "-f",
    type=Path,
    help="The file to sign.",
    required=False,
)
@click.option("--transaction", "-t", type=str, help="The transaction to sign.", required=False)
@click.option("--output", "-o", type=Path, help="The output file.", required=False)
@click.option("--force", is_flag=True, help="Force signing without confirmation.", required=False)
def sign(*, account: str, file: Path | None, transaction: str | None, output: Path | None, force: bool) -> None:
    signer_account = get_account_with_private_key(account)

    if bool(file) == bool(transaction):
        raise click.ClickException("Provide either a file to sign or a transaction to sign, not both or none.")

    txn: Transaction = get_transaction(file, transaction)

    if not force and not confirm_transaction(txn):
        return

    sign_and_output_transaction(txn, signer_account.private_key, output)
