import logging

import click

from algokit.core.compile.python import find_valid_puyapy_command
from algokit.core.proc import run

logger = logging.getLogger(__name__)


class CompileGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        command_dict = {"py": "python"}
        if cmd_name in command_dict:
            return click.Group.get_command(self, ctx, command_dict[cmd_name])

        return None


@click.group("compile", cls=CompileGroup, hidden=True)
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
    "python",
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
        click.secho(
            "An error occurred during compile. Ensure supplied files are valid PuyaPy code before retrying.",
            err=True,
            fg="red",
        )
        raise click.exceptions.Exit(run_result.exit_code)
