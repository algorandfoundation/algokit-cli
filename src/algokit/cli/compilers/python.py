import logging
import os
from collections.abc import Callable
from typing import Any

import click

from algokit.core.compilers.python import find_valid_puyapy_command
from algokit.core.proc import run

logger = logging.getLogger(__name__)
_AnyCallable = Callable[..., Any]


def invoke_puyapy(context: click.Context, puyapy_args: list[str]) -> None:
    version = str(context.obj["version"]) if context.obj["version"] else None

    puyapy_command = find_valid_puyapy_command(version)

    run_result = run(
        [
            *puyapy_command,
            *puyapy_args,
        ],
        env=(dict(os.environ) | {"NO_COLOR": "1"}) if context.color is False else None,
    )
    click.echo(run_result.output)

    if run_result.exit_code != 0:
        click.secho(
            "An error occurred during compile. Please ensure that any supplied arguments are valid "
            "and any files passed are valid Algorand Python code before retrying.",
            err=True,
            fg="red",
        )
        raise click.exceptions.Exit(run_result.exit_code)


def common_puyapy_command_options(function: _AnyCallable) -> click.Command:
    function = click.argument("puyapy_args", nargs=-1, type=click.UNPROCESSED)(function)
    function = click.pass_context(function)
    return click.command(
        context_settings={
            "ignore_unknown_options": True,
        },
        add_help_option=False,
        help="Compile Algorand Python contract(s) using the PuyaPy compiler.",
    )(function)


@common_puyapy_command_options
def python(context: click.Context, puyapy_args: list[str]) -> None:
    invoke_puyapy(context, puyapy_args)


@common_puyapy_command_options
def py(context: click.Context, puyapy_args: list[str]) -> None:
    invoke_puyapy(context, puyapy_args)
