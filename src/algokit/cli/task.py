import logging

import click

from algokit.cli.tasks.vanity_address import vanity_address
from algokit.cli.tasks.wallet import wallet

logger = logging.getLogger(__name__)


@click.group(name="task")
def task_group() -> None:
    """Collection of useful tasks to help you develop on Algorand."""


task_group.add_command(wallet)
task_group.add_command(vanity_address)
