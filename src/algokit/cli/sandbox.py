import logging
import os

import click

from algokit.core.sandbox import get_docker_compose_yml
from algokit.core.utils import app_config, exec
logger = logging.getLogger(__name__)


@click.group("sandbox", short_help="Manage the Algorand sandbox")
def sandbox_group():
    exec.run(
        "docker",
        suppress_output=True,
        throw_on_error="Docker not found; please install Docker and add to path. "
        + "See https://docs.docker.com/get-docker/ for more information.",
    )
    exec.run(
        "docker-compose",
        suppress_output=True,
        throw_on_error="Docker Compose not found; please install Docker Compose and add to path. "
        + "See https://docs.docker.com/compose/install/ for more information.",
    )


@sandbox_group.command("start")
def start_sandbox():
    click.echo("Starting the AlgoKit sandbox now...")
    app_config.write("docker-compose.yml", get_docker_compose_yml())
    exec.run("docker-compose up -d", app_config.get_config_dir(), throw_on_error="Error starting sandbox")
    click.echo("Started; execute `algokit sandbox status` to check the status.")


@sandbox_group.command("restart")
def restart_sandbox():
    logger.info("Restarting the sandbox now...")
    # TODO: the thing
    logger.info("Done!")
