import click

from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group
from algokit.cli.version import version


@click.group()
def cli():
    pass


cli.add_command(init_command)
cli.add_command(sandbox_group)
cli.add_command(version)


if __name__ == "__main__":
    cli()
