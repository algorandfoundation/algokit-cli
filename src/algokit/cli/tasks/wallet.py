import json
import re

import click
from algosdk import account, encoding, mnemonic

from algokit.core.tasks.wallet import add_alias, get_alias, get_aliases, remove_alias


@click.group()
def wallet() -> None:
    """Wallet related commands."""


@wallet.command("add")
@click.argument("alias_name", type=click.STRING)
@click.option("--address", "-a", type=click.STRING, required=True, help="The address of the account")
@click.option(
    "--mnemonic",
    "-m",
    "use_mnemonic",
    is_flag=True,
    help="If specified then prompt the user for a mnemonic phrase interactively using masked input",
)
def add(*, alias_name: str, address: str, use_mnemonic: bool) -> None:
    """Add an address or account to be stored against a named alias."""
    # Validate alias_name
    if not re.match(r"^[\w-]{1,20}$", alias_name):
        raise click.ClickException(
            "Invalid alias name. It must conform to have at most 20 symbols consisting of numbers, "
            "letters, dashes or underscores"
        )

    # Validate address
    if not encoding.is_valid_address(address):  # type: ignore[no-untyped-call]
        raise click.ClickException("Invalid address. Please provide a valid Algorand address.")

    # If mnemonic flag is provided, prompt the user for a mnemonic phrase interactively using masked input
    private_key = None

    if use_mnemonic:
        mnemonic_phrase = click.prompt(
            "Please enter the mnemonic phrase (25 words with whitespace separator)", hide_input=True
        )
        # Validate mnemonic
        try:
            private_key = mnemonic.to_private_key(mnemonic_phrase)  # type: ignore[no-untyped-call]
        except ValueError as err:
            raise click.ClickException("Invalid mnemonic. Please provide a valid Algorand mnemonic.") from err

        # Check if the address from the mnemonic matches the provided address
        mnemonic_address = account.address_from_private_key(private_key)  # type: ignore[no-untyped-call]
        if mnemonic_address != address:
            click.echo(
                "Warning: The address from the mnemonic doesn`t match the provided address. "
                "It won`t work unless that account has been rekeyed."
            )

    if get_alias(alias_name):
        response = click.prompt(
            f"Alias {alias_name} already exists. Do you want to overwrite it? (y/n)",
            type=click.Choice(["y", "n"]),
            default="n",
        )
        if response == "n":
            return

    add_alias(alias_name, address, private_key)

    click.echo(f"Alias `{alias_name}` added successfully.")


@wallet.command("get")
@click.argument("alias", type=click.STRING)
def get(alias: str) -> None:
    """Get an address or account stored against a named alias."""
    alias_data = get_alias(alias)

    if not alias_data:
        raise click.ClickException(f"Alias `{alias}` does not exist.")

    click.echo(
        f"Address for alias `{alias}`: {alias_data.address}"
        f"{' (🔐 includes private key)' if alias_data.private_key else ''}"
    )


@wallet.command("list")
def list_all() -> None:
    """List all addresses or accounts stored against a named alias."""

    aliases = get_aliases()

    output = [
        {
            "alias": alias_data.alias,
            "address": alias_data.address,
            "has_private_key": bool(alias_data.private_key),
        }
        for alias_data in aliases
    ]

    click.echo(json.dumps(output, indent=2))


@wallet.command("remove")
@click.argument("alias", type=click.STRING)
def remove(alias: str) -> None:
    """Remove an address or account stored against a named alias."""
    alias_data = get_alias(alias)

    if not alias_data:
        raise click.ClickException(f"Alias `{alias}` does not exist.")

    remove_alias(alias)

    click.echo(f"Alias `{alias}` removed successfully.")


@wallet.command("reset")
def reset() -> None:
    """Remove all aliases."""
    aliases = get_aliases()

    if not aliases:
        click.echo("Warning: No aliases available to reset.")
        return

    response = click.prompt(
        "🚨 This is a destructive action that will clear all aliases. Are you sure?",
        type=click.Choice(["y", "n"]),
        default="n",
    )

    if response == "n":
        return

    for alias_data in aliases:
        remove_alias(alias_data.alias)

    click.echo("All aliases have been cleared.")
