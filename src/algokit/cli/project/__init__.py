import click

from algokit.cli.project.bootstrap import bootstrap_group
from algokit.cli.project.deploy import deploy_command
from algokit.cli.project.link import link_command
from algokit.cli.project.list import list_command
from algokit.cli.project.run import run_group


@click.group(
    "project",
)
def project_group() -> None:
    """Provides a suite of commands for managing your AlgoKit project.
    This includes initializing project dependencies, deploying smart contracts,
    and executing predefined or custom commands within your project environment."""


project_group.add_command(deploy_command)
project_group.add_command(bootstrap_group)
project_group.add_command(run_group)
project_group.add_command(list_command)
project_group.add_command(link_command)
