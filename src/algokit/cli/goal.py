import logging

import click
from algokit.core import proc

logger = logging.getLogger(__name__)


@click.command(
    "goal",
    short_help="Run the Algorand goal CLI against the AlgoKit Sandbox.",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.option(
    "--console/--no-console",
    help="Open a Bash console so you can execute multiple goal commands and/or interact with a filesystem.",
    default=False,
)
@click.argument("goal_args", nargs=-1, type=click.UNPROCESSED)
def goal_command(console: bool, goal_args: list[str]) -> None:  # noqa: FBT001
    try:
        proc.run(["docker", "version"], bad_return_code_error_message="Docker engine isn't running; please start it.")
    except IOError as ex:
        # an IOError (such as PermissionError or FileNotFoundError) will only occur if "docker"
        # isn't an executable in the user's path, which means docker isn't installed
        raise click.ClickException(
            "Docker not found; please install Docker and add to path.\n"
            "See https://docs.docker.com/get-docker/ for more information."
        ) from ex
    if console:
        logger.info("Opening Bash console on the algod node; execute `exit` to return to original console")
        result = proc.run_interactive("docker exec -it -w /root algokit_algod bash".split())
        if result.exit_code != 0:
            raise click.ClickException(
                "Error executing goal;" + " ensure the Sandbox is started by executing `algokit sandbox status`"
            )

    else:
        cmd = str("docker exec algokit_algod goal").split()
        cmd.extend(goal_args)
        proc.run(
            cmd,
            stdout_log_level=logging.INFO,
            prefix_process=False,
            bad_return_code_error_message="Error executing goal;"
            + " ensure the Sandbox is started by executing `algokit sandbox status`",
        )
