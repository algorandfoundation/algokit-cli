from importlib import metadata

import click


@click.command("version", short_help="Show current version of AlgoKit cli")
def version_command():
    click.echo(metadata.version("algokit"))
