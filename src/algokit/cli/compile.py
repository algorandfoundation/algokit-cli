import logging

import click

from algokit.core.compile import find_valid_puyapy_command
from algokit.core.proc import run

logger = logging.getLogger(__name__)


@click.group("compile", hidden=True)
@click.option(
    "-v",
    "--version",
    "version",
    required=False,
    default=None,
    help=(
        "Compiler version, for example, 1.0.0. "
        "If the version isn't specified, AlgoKit will check if the compiler is installed locally, and execute that. "
        "If the compiler is not found, it will install the latest version. "
        "If the version is specified, AlgoKit will check if the local compiler's version satisfies, and execute that. "
        "Otherwise, AlgoKit will install the specifed compiler version."
    ),
)
@click.pass_context
def compile_group(context: click.Context, version: str | None) -> None:
    """Compile high level language smart contracts to TEAL"""
    context.ensure_object(dict)
    context.obj["version"] = version


@compile_group.command(
    "py",
    short_help="Compile Python to TEAL with PuyaPy",
    help="Compile Python to TEAL with PuyaPy, review https://github.com/algorandfoundation/puya for usage",
    context_settings={
        "ignore_unknown_options": True,
    },
    add_help_option=False,
)
@click.argument("puya_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def compile_py_command(context: click.Context, puya_args: list[str]) -> None:
    """
    Compile Python contract(s) to TEAL with PuyaPy
    """
    version = str(context.obj["version"]) if context.obj["version"] else None

    puya_command = find_valid_puyapy_command(version)

    run_result = run(
        [
            *puya_command,
            *puya_args,
        ],
    )
    click.echo(run_result.output)

    if run_result.exit_code != 0:
        raise click.exceptions.Exit(run_result.exit_code)
