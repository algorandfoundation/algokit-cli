import logging

import click

from algokit.cli.task.asset import transfer

logger = logging.getLogger(__name__)


@click.group(name="task")
def task_group() -> None:
    """Utils for an Algorand project."""


task_group.add_command(transfer)
