import logging

import click

from algokit.cli.tasks.assets import opt_in_function

logger = logging.getLogger(__name__)


@click.group(name="task")
def task_group() -> None:
    """Collection of useful tasks to help you develop on Algorand."""


task_group.add_command(opt_in_function)
