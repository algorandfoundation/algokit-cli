import json
import logging
import re
from pathlib import Path

import click

from algokit.core.tasks.vanity_address import MatchType, VanityAccount, generate_vanity_address
from algokit.core.tasks.wallet import WALLET_ALIASING_MAX_LIMIT, WalletAliasingLimitError, add_alias, get_alias

logger = logging.getLogger(__name__)


def _validate_inputs(
    keyword: str,
    output: str,
    alias: str | None,
    output_file: Path | None,
) -> None:
    if not re.match("^[A-Z2-7]+$", keyword):
        raise click.ClickException("Invalid KEYWORD. Allowed: uppercase letters A-Z and numbers 2-7.")
    if output == "alias" and not alias:
        raise click.ClickException(
            "Please provide an alias using the '--alias' option when the output is set to 'alias'."
        )
    if output == "file" and not output_file:
        raise click.ClickException(
            "Please provide an output filename using the '--file-path' option when the output is set to 'file'."
        )


def _store_vanity_to_alias(*, alias: str, vanity_account: VanityAccount, force: bool) -> None:
    logger.info(f"Adding {vanity_account.address} to wallet alias named {alias}")
    if get_alias(alias) and not force:
        response = click.prompt(
            f"Alias '{alias}' already exists. Overwrite?",
            type=click.Choice(["y", "n"]),
            default="n",
        )
        if response == "n":
            return

    try:
        add_alias(alias, vanity_account.address, vanity_account.private_key)
    except WalletAliasingLimitError as ex:
        raise click.ClickException(f"Reached the max of {WALLET_ALIASING_MAX_LIMIT} aliases.") from ex
    except Exception as ex:
        raise click.ClickException("Failed to add alias") from ex
    else:
        click.echo(f"Alias '{alias}' added successfully.")


@click.command(
    name="vanity-address",
    help="""Generate a vanity Algorand address. Your KEYWORD can only include letters A - Z and numbers 2 - 7.
    Keeping your KEYWORD under 5 characters will usually result in faster generation.
    Note: The longer the KEYWORD, the longer it may take to generate a matching address.
    Please be patient if you choose a long keyword.
    """,
)
@click.argument("keyword")
@click.option(
    "--match",
    "-m",
    default=MatchType.START.value,
    type=click.Choice([e.value for e in MatchType]),
    help="Location where the keyword will be included. Default is start.",
)
@click.option(
    "--output",
    "-o",
    required=False,
    default="stdout",
    type=click.Choice(["stdout", "alias", "file"]),
    help="How the output will be presented.",
)
@click.option(
    "--alias",
    "-a",
    required=False,
    default=None,
    help='Alias for the address. Required if output is "alias".',
    type=click.STRING,
)
@click.option(
    "--file-path",
    "output_file_path",
    required=False,
    default=None,
    type=click.Path(dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    help='File path where to dump the output. Required if output is "file".',
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    required=False,
    default=False,
    type=click.BOOL,
    help="Allow overwriting an aliases without confirmation, if output option is 'alias'.",
)
def vanity_address(  # noqa: PLR0913
    *,
    keyword: str,
    match: MatchType,
    output: str,
    alias: str | None,
    output_file_path: Path | None,
    force: bool,
) -> None:
    if output_file_path and output != "file":
        raise click.ClickException("File path can only be set when the output is set to 'file'.")
    if alias and output != "alias":
        raise click.ClickException("Alias can only be set when the output is set to 'alias'.")

    match = MatchType(match)  # Force cast since click does not yet support enums as types
    _validate_inputs(keyword, output, alias, output_file_path)

    try:
        vanity_account = generate_vanity_address(keyword, match)
    except KeyboardInterrupt as ex:
        click.echo("\nAborting vanity address generation...")
        raise click.Abort from ex

    if output == "stdout":
        logger.warning(
            "WARNING: Your mnemonic is displayed on the console. "
            "Ensure its security by keeping it confidential."
            "Consider clearing your terminal history after noting down the token.\n"
        )
        click.echo(vanity_account.__dict__)

    elif output == "alias" and alias:
        _store_vanity_to_alias(alias=alias, vanity_account=vanity_account, force=force)
    elif output == "file" and output_file_path is not None:
        with output_file_path.open("w") as f:
            json.dump(vanity_account.__dict__, f, indent=4)
            click.echo(f"Output written to {output_file_path.absolute()}")
