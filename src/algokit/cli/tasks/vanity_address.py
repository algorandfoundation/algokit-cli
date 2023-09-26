import json
import logging
import re
from pathlib import Path

import click

from algokit.core.tasks.vanity_address import MatchType, generate_vanity_address

logger = logging.getLogger(__name__)


def validate_inputs(
    keyword: str,
    output: str,
    alias: str | None,
    output_file: str | None,
) -> None:
    if not re.match("^[A-Z2-7]+$", keyword):
        raise click.ClickException("Invalid KEYWORD. Allowed: uppercase letters A-Z and numbers 2-7.")
    if output == "alias" and not alias:
        raise click.ClickException(
            "Please provide an alias using the '--alias' option when the output is set to 'alias'."
        )
    if output == "file" and not output_file:
        raise click.ClickException(
            "Please provide an output filename using the '--output-file' option when the output is set to 'file'."
        )


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
@click.option("--alias", "-a", required=False, help='Alias for the address. Required if output is "alias".')
@click.option(
    "--output-file",
    "-f",
    required=False,
    type=click.Path(),
    help='File to dump the output. Required if output is "file".',
)
def vanity_address(
    keyword: str, match: MatchType, output: str, alias: str | None = None, output_file: str | None = None
) -> None:
    match = MatchType(match)  # Force cast since click does not yet support enums as types
    validate_inputs(keyword, output, alias, output_file)

    result_data = generate_vanity_address(keyword, match)

    if output == "stdout":
        logger.warning(
            "WARNING: Your mnemonic is displayed on the console. "
            "Ensure its security by keeping it confidential."
            "Consider clearing your terminal history after noting down the token.\n"
        )
        click.echo(result_data)

    elif output == "alias" and alias is not None:
        add_to_wallet(alias, result_data)
    elif output == "file" and output_file is not None:
        output_path = Path(output_file)
        with output_path.open("w") as f:
            json.dump(result_data, f, indent=4)
            click.echo(f"Output written to {output_path.absolute()}")


def add_to_wallet(alias: str, output_data: dict) -> None:
    logger.info(f"Adding {output_data} to wallet {alias}")
