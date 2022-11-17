import logging

import click

from algokit.core import conf, exec
from algokit.core.sandbox import get_docker_compose_yml

logger = logging.getLogger(__name__)


@click.group("sandbox", short_help="Manage the AlgoKit sandbox")
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
    exec.run("docker ps", suppress_output=True, throw_on_error="Docker engine isn't running; please start it. ")


@sandbox_group.command("start", short_help="Start the AlgoKit sandbox")
def start_sandbox():
    logger.info("Starting the AlgoKit sandbox now...")
    conf.write_config("docker-compose.yml", get_docker_compose_yml())
    exec.run("docker-compose up -d", conf.get_app_config_dir(), throw_on_error="Error starting sandbox")
    logger.info("Started; execute `algokit sandbox status` to check the status.")
