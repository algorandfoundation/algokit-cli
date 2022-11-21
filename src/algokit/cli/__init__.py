import sys

import click
from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group
from algokit.core.conf import PACKAGE_NAME
from algokit.core.log_handlers import output_options, get_colour_pref_from_args


@click.group(
    help="AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(package_name=PACKAGE_NAME)
@output_options
@click.pass_context
def algokit(ctx: click.Context) -> None:
    # wondering why we are accessing sys.argv manually?
    # see HACK note in source file for the below function to find out!
    ctx.color = get_colour_pref_from_args(sys.argv)


algokit.add_command(init_command)
algokit.add_command(sandbox_group)
