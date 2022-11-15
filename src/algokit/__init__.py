import click
import sys
import logging

from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group
from algokit.cli.version import version

class ConfigurationError(Exception):
    pass

@click.group()
def cli():
    check_python_version()

def check_python_version():
    installed_python_version = sys.version_info
    logging.debug(f'Python version {installed_python_version.major}.{installed_python_version.minor}.{installed_python_version.micro} installed')
    if installed_python_version < (3, 10):
        raise ConfigurationError(f'AlgoKit CLI requires python v3.10.1 or higher to be installed. Your installed version is {installed_python_version.major}.{installed_python_version.minor}.{installed_python_version.micro} Please visit https://www.python.org/downloads/ and install most recent version')


cli.add_command(init_command)
cli.add_command(sandbox_group)
cli.add_command(version)


if __name__ == "__main__":
    cli()
