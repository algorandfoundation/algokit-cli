import logging
import re

import click

from algokit.cli.project.bootstrap import bootstrap_group
from algokit.cli.project.deploy import deploy_command
from algokit.cli.project.link import link_command
from algokit.cli.project.list import list_command
from algokit.cli.project.run import run_group
from algokit.core import proc

logger = logging.getLogger(__name__)


@click.group(
    "project",
)
def project_group() -> None:
    """Provides a suite of commands for managing your AlgoKit project.
    This includes initializing project dependencies, deploying smart contracts,
    and executing predefined or custom commands within your project environment."""
    try:
        poetry_version_result = proc.run(
            ["poetry", "--version"],
        )
    except Exception:
        return

    if re.search(r"1\.\d+\.\d+", poetry_version_result.output):
        logger.warning(
            "You are using Poetry 1.x, which is deprecated. "
            "Please upgrade to Poetry 2.x for better support and features."
        )


project_group.add_command(deploy_command)
project_group.add_command(bootstrap_group)
project_group.add_command(run_group)
project_group.add_command(list_command)
project_group.add_command(link_command)
