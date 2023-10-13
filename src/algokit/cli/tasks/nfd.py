import logging

import click

from algokit.cli.tasks.utils import validate_address
from algokit.core.tasks.nfd import NFDMatchType, nfd_lookup_by_address, nfd_lookup_by_domain

logger = logging.getLogger(__name__)


def is_nfd(value: str) -> bool:
    return value.endswith(".algo")


def is_algorand_address(value: str) -> bool:
    try:
        validate_address(value)
        return True
    except Exception:
        return False


@click.command(
    name="nfd-lookup",
    help="Perform a lookup via NFD domain or address, returning the associated address or domain respectively.",
)
@click.argument(
    "value",
    type=click.STRING,
)
@click.option(
    "--output",
    "-o",
    required=False,
    default=NFDMatchType.ADDRESS.value,
    type=click.Choice([e.value for e in NFDMatchType]),
    help="Output format for NFD API response. Defaults to address|domain resolved.",
)
def nfd_lookup(
    value: str,
    output: str,
) -> None:
    if not is_nfd(value) and not is_algorand_address(value):
        raise click.ClickException("Invalid input. Must be either a valid NFD domain or an Algorand address.")

    try:
        if is_nfd(value):
            click.echo(nfd_lookup_by_domain(value, NFDMatchType(output)))
        elif is_algorand_address(value):
            click.echo(nfd_lookup_by_address(value, NFDMatchType(output)))
    except Exception as err:
        raise click.ClickException(str(err)) from err
