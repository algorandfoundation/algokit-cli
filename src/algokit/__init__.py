import click

from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group


@click.group()
def cli():
    pass


cli.add_command(init_command)
cli.add_command(sandbox_group)


if __name__ == "__main__":
    cli()
