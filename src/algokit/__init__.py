import click
import sys
import logging

from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group
from algokit.cli.version import version_command


class ConfigurationError(Exception):
    pass


CLICK_CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(
    help="AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.",
    invoke_without_command=True,
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.option("--version", help="Show current version of AlgoKit cli", is_flag=True)
@click.pass_context
def cli(ctx, version):
    check_python_version()
    if version:
        ctx.invoke(version_command)
        return

    # The help output would normally show when no subcommands have been supplied,
    # but we override the default behavior through the invoke_without_command so we can show 'algokit --version'
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


def check_python_version():
    installed_python_version = sys.version_info
    logging.debug(
        f"Python version "
        f"{installed_python_version.major}.{installed_python_version.minor}.{installed_python_version.micro} installed"
    )
    if installed_python_version > (3, 10):
        raise ConfigurationError(
            f"Unsupported CPython version "
            f"({installed_python_version.major}.{installed_python_version.minor}.{installed_python_version.micro}) "
            f"detected. The minimum version of Python supported is CPython 3.10.\n\nIf you need help installing then "
            f"this is a good starting point: https://www.python.org/about/gettingstarted/."
        )


cli.add_command(init_command)
cli.add_command(sandbox_group)
cli.add_command(version_command)


if __name__ == "__main__":
    try:
        cli()
    except ConfigurationError as ce:
        logging.error(f"Configuration error: {str(ce)}")
        sys.exit(1)
