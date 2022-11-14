import click
from importlib import metadata

@click.command("version", short_help="Show current version of AlgoKit cli")
def version():
    print(metadata.version('algokit'))
