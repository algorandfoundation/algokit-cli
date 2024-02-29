import logging

import click

from algokit.core.compile import find_valid_puyapy_command
from algokit.core.proc import run

logger = logging.getLogger(__name__)


@click.group("compile")
def compile_group() -> None:
    """Compile high level language smart contracts to TEAL"""


@compile_group.command(
    "py",
    short_help="Compile Python to TEAL with PuyaPy",
    help="Compile Python to TEAL with PuyaPy, review https://github.com/algorandfoundation/puya for usage",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.option(
    "-v",
    "--version",
    "version",
    required=False,
    default=None,
    help=("PuyaPy compiler version. Default to latest"),
)
@click.argument("puya_args", nargs=-1, type=click.UNPROCESSED)
def compile_py_command(version: str | None, puya_args: list[str]) -> None:
    """
    Compile Python contract(s) to TEAL with PuyaPy
    """

    puya_command = find_valid_puyapy_command(version)

    run(
        [
            *puya_command,
            *puya_args,
        ],
        bad_return_code_error_message=("PuyaPy failed to compile the contract(s)"),
    )
