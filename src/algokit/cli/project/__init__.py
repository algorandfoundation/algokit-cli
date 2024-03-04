import click

from algokit.cli.project.bootstrap import bootstrap_group
from algokit.cli.project.deploy import deploy_command
from algokit.cli.project.run import run_group


@click.group(
    "project",
)
def project_group() -> None:
    """Define custom project specific commands to run via cli or, manage bootstrap of dependencies and
    deployment of smart contracts in your project."""


project_group.add_command(deploy_command)
project_group.add_command(bootstrap_group)
project_group.add_command(run_group)
