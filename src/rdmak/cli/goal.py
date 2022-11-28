import logging

import click
from rdmak.core import exec

logger = logging.getLogger(__name__)


@click.command(
    "goal",
    short_help="Run the Algorand goal CLI against the AlgoKit Sandbox",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.argument("goal_args", nargs=-1, type=click.UNPROCESSED)
def goal_command(goal_args: list[str]) -> None:
    try:
        exec.run(["docker", "version"], bad_return_code_error_message="Docker engine isn't running; please start it.")
    except IOError as ex:
        # an IOError (such as PermissionError or FileNotFoundError) will only occur if "docker"
        # isn't an executable in the user's path, which means docker isn't installed
        raise click.ClickException(
            "Docker not found; please install Docker and add to path.\n"
            "See https://docs.docker.com/get-docker/ for more information."
        ) from ex
    cmd = str("docker exec algokit_algod goal").split()
    cmd.extend(goal_args)
    exec.run(
        cmd,
        stdout_log_level=logging.INFO,
        prefix_process=False,
        bad_return_code_error_message="Error executing goal;"
        + " ensure the Sandbox is started by executing `algokit sandbox start`",
    )
