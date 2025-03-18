import logging
import os
from collections.abc import Callable
from typing import Any

import click

from algokit.core.compilers.typescript import find_valid_puyats_command
from algokit.core.proc import run
from algokit.core.utils import extract_semantic_version

logger = logging.getLogger(__name__)
_AnyCallable = Callable[..., Any]


def invoke_puyats(context: click.Context, puyats_args: list[str]) -> None:
    version = extract_semantic_version(str(context.obj["version"])) if context.obj["version"] else None

    puyats_command = find_valid_puyats_command(version)

    run_result = run(
        [
            *puyats_command,
            *puyats_args,
        ],
        env=(dict(os.environ) | {"NO_COLOR": "1"}) if context.color is False else None,
    )
    click.echo(run_result.output)

    if run_result.exit_code != 0:
        click.secho(
            "An error occurred during compile. Please ensure that any supplied arguments are valid "
            "and any files passed are valid Algorand TypeScript code before retrying.",
            err=True,
            fg="red",
        )
        raise click.exceptions.Exit(run_result.exit_code)


def common_puyats_command_options(function: _AnyCallable) -> click.Command:
    function = click.argument("puyats_args", nargs=-1, type=click.UNPROCESSED)(function)
    function = click.pass_context(function)
    return click.command(
        context_settings={
            "ignore_unknown_options": True,
        },
        add_help_option=False,
        help="Compile Algorand TypeScript contract(s) using the PuyaTs compiler.",
    )(function)


@common_puyats_command_options
def typescript(context: click.Context, puyats_args: list[str]) -> None:
    invoke_puyats(context, puyats_args)


@common_puyats_command_options
def ts(context: click.Context, puyats_args: list[str]) -> None:
    invoke_puyats(context, puyats_args)
