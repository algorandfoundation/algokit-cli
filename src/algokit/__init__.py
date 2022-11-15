import click
import sys
import logging

from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group
from algokit.cli.version import version

class ConfigurationError(Exception):
    pass

@click.group(help='AlgoKit is your one stop shop to develop applications on the Algorand blockchain.')
def cli():
    check_python_version()

def check_python_version():
    installed_python_version = sys.version_info
    logging.debug(f'Python version {installed_python_version.major}.{installed_python_version.minor}.{installed_python_version.micro} installed')
    if installed_python_version < (3, 10):
        raise ConfigurationError(f'Unsupported CPython version ({installed_python_version.major}.{installed_python_version.minor}.{installed_python_version.micro}) detected. The minimum version of Python supported is CPython 3.10.\n\nIf you need help installing then this is a good starting point: https://www.python.org/about/gettingstarted/.')

cli.add_command(init_command)
cli.add_command(sandbox_group)
cli.add_command(version)


if __name__ == "__main__":
    try:
        cli()
    except ConfigurationError as ce:
        logging.error(f'Configuration error: {str(ce)}')
        sys.exit(1)

