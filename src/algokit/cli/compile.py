import logging

import click

from algokit.cli.compilers.python import py, python

logger = logging.getLogger(__name__)


@click.group(
    "compile",
    short_help=(
        "Compile smart contracts and smart signatures written in a supported high-level language "
        "to a format deployable on the Algorand Virtual Machine (AVM)."
    ),
)
@click.option(
    "-v",
    "--version",
    "version",
    required=False,
    default=None,
    help=(
        "The compiler version to pin to, for example, 1.0.0. "
        "If no version is specified, AlgoKit checks if the compiler is installed and runs the installed version. "
        "If the compiler is not installed, AlgoKit runs the latest version. "
        "If a version is specified, AlgoKit checks if an installed version matches and runs the installed version. "
        "Otherwise, AlgoKit runs the specified version."
    ),
)
@click.pass_context
def compile_group(context: click.Context, version: str | None) -> None:
    """
    Compile smart contracts and smart signatures written in a supported high-level language
    to a format deployable on the Algorand Virtual Machine (AVM).
    """
    context.ensure_object(dict)
    context.obj["version"] = version


compile_group.add_command(python, "python")
compile_group.add_command(py, "py")
