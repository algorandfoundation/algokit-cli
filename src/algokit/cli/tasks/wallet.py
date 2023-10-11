import json
import re

import click
from algosdk import account

from algokit.cli.tasks.utils import get_private_key_from_mnemonic, validate_address
from algokit.core.tasks.wallet import (
    WALLET_ALIASING_MAX_LIMIT,
    WalletAliasingLimitError,
    add_alias,
    get_alias,
    get_aliases,
    remove_alias,
)


def _validate_alias_name(alias_name: str) -> None:
    pattern = r"^[\w-]{1,20}$"
    if not re.match(pattern, alias_name):
        raise click.ClickException(
            "Invalid alias name. It should have at most 20 characters consisting of numbers, "
            "letters, dashes, or underscores."
        )


@click.group()
def wallet() -> None:
    """Create short aliases for your addresses and accounts on AlgoKit CLI."""


@wallet.command("add")
@click.argument("alias_name", type=click.STRING)
@click.option("--address", "-a", type=click.STRING, required=True, help="The address of the account.")
@click.option(
    "--mnemonic",
    "-m",
    "use_mnemonic",
    is_flag=True,
    help="If specified then prompt the user for a mnemonic phrase interactively using masked input.",
)
@click.option("--force", "-f", is_flag=True, help="Allow overwriting an existing alias.", type=click.BOOL)
def add(*, alias_name: str, address: str, use_mnemonic: bool, force: bool) -> None:
    """Add an address or account to be stored against a named alias (at most 50 aliases)."""

    _validate_alias_name(alias_name)
    validate_address(address)

    private_key = get_private_key_from_mnemonic() if use_mnemonic else None

    if use_mnemonic:
        derived_address = account.address_from_private_key(private_key)  # type: ignore[no-untyped-call]
        if derived_address != address:
            click.echo(
                "Warning: Address from the mnemonic doesn't match the provided address. "
                "It won't work unless the account has been rekeyed."
            )

    if get_alias(alias_name) and not force:
        response = click.prompt(
            f"Alias '{alias_name}' already exists. Overwrite?",
            type=click.Choice(["y", "n"]),
            default="n",
        )
        if response == "n":
            return

    try:
        add_alias(alias_name, address, private_key)
    except WalletAliasingLimitError as ex:
        raise click.ClickException(f"Reached the max of {WALLET_ALIASING_MAX_LIMIT} aliases.") from ex
    except Exception as ex:
        raise click.ClickException("Failed to add alias") from ex
    else:
        click.echo(f"Alias '{alias_name}' added successfully.")


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
    """List all addresses and accounts stored against a named alias."""

    aliases = get_aliases()

    output = [
        {
            "alias": alias_data.alias,
            "address": alias_data.address,
            "has_private_key": bool(alias_data.private_key),
        }
        for alias_data in aliases
    ]

    content = (
        json.dumps(output, indent=2)
        if output
        else "You don't have any aliases stored yet. Create one using `algokit task wallet add`."
    )

    click.echo(content)


@wallet.command("remove")
@click.argument("alias", type=click.STRING)
@click.option("--force", "-f", is_flag=True, help="Allow removing an alias without confirmation.")
def remove(*, alias: str, force: bool) -> None:
    """Remove an address or account stored against a named alias."""

    alias_data = get_alias(alias)

    if not alias_data:
        raise click.ClickException(f"Alias `{alias}` does not exist.")

    if not force:
        response = click.prompt(
            f"🚨 This is a destructive action that will remove the `{alias_data.alias}` alias. Are you sure?",
            type=click.Choice(["y", "n"]),
            default="n",
        )

        if response == "n":
            return

    remove_alias(alias)

    click.echo(f"Alias `{alias}` removed successfully.")


@wallet.command("reset")
@click.option("--force", "-f", is_flag=True, help="Allow removing all aliases without confirmation.")
def reset(*, force: bool) -> None:
    """Remove all aliases."""

    aliases = get_aliases()

    if not aliases:
        click.echo("Warning: No aliases available to reset.")
        return

    if not force:
        response = click.prompt(
            "🚨 This is a destructive action that will clear all aliases. Are you sure?",
            type=click.Choice(["y", "n"]),
            default="n",
        )

        if response == "n":
            return

    for alias_data in aliases:
        try:
            remove_alias(alias_data.alias)
        except Exception as ex:
            raise click.ClickException(f"Failed to remove alias {alias_data.alias}") from ex

    click.echo("All aliases have been cleared.")
