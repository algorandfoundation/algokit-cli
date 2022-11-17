import logging

import click

logger = logging.getLogger(__name__)


@click.group("sandbox", short_help="Manage the Algorand sandbox")
def sandbox_group():
    logger.debug("Hello I'm the sandbox command group")


@sandbox_group.command("restart")
def restart_sandbox():
    logger.info("Restarting the sandbox now...")
    # TODO: the thing
    logger.info("Done!")
