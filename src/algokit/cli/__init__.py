import logging

import click

from algokit.core.conf import PACKAGE_NAME
from algokit.core.log_handlers import console_log_handler
from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group


@click.group(
    help="AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(package_name=PACKAGE_NAME)
@click.option("--verbose", "-v", is_flag=True)
@click.option("--color/--no-color", default=None)
def algokit(verbose: bool, color: bool | None):
    if verbose:
        console_log_handler.setLevel(logging.DEBUG)
    if color is not None:
        console_log_handler.force_styles_to = color


algokit.add_command(init_command)
algokit.add_command(sandbox_group)
