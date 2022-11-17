import platform
import sys

import click

# this isn't beautiful, but to avoid confusing user errors we need this check before we start importing our own modules
if sys.version_info < (3, 10, 0):
    click.echo(
        click.style(
            f"Unsupported CPython version: {platform.python_version()} detected.\n"
            "The minimum version of Python supported is CPython 3.10.\n"
            "If you need help installing then this is a good starting point: \n"
            "https://www.python.org/about/gettingstarted/",
            fg="red",
        ),
        err=True,
    )
    sys.exit(-1)

from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group


@click.group(
    help="AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(package_name="algokit")
@click.pass_context
def cli():
    pass


cli.add_command(init_command)
cli.add_command(sandbox_group)


if __name__ == "__main__":
    cli()
