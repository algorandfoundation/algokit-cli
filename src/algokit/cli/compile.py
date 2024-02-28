import logging

import click

from algokit.core.proc import run
from algokit.core.utils import find_valid_pipx_command

logger = logging.getLogger(__name__)


@click.group("compile")
def compile_group() -> None:
    """Compile smart contracts to TEAL"""


@compile_group.command(
    "py",
    short_help="Compile Python to TEAL with Puyapy",
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
    help=("Puyapy compiler version. " "Default to latest"),
)
@click.argument("puya_args", nargs=-1, type=click.UNPROCESSED)
def compile_py_command(version: str | None, puya_args: list[str]) -> None:
    """
    Compile Python contract(s) with Puyapy
    """

    pipx_command = find_valid_pipx_command(
        "Unable to find pipx install so that `Puyapy` compiler can be installed; "
        "please install pipx via https://pypa.github.io/pipx/ "
        "and then try `algokit compile py ...` again."
    )
    run(
        [
            *pipx_command,
            "run",
            "puya" if version is None else f"puya=={version}",
            *puya_args,
        ],
        bad_return_code_error_message=("Puyapy failed to compile the contract(s)"),
    )
