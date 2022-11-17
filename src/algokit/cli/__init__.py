import click

from algokit.cli.init import init_command
from algokit.cli.sandbox import sandbox_group


@click.group(
    help="AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(package_name="algokit")
def algokit():
    pass


algokit.add_command(init_command)
algokit.add_command(sandbox_group)
