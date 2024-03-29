import logging

import click

from algokit.core import proc
from algokit.core.goal import (
    get_volume_mount_path_docker,
    get_volume_mount_path_local,
    post_process,
    preprocess_command_args,
)
from algokit.core.sandbox import DEFAULT_NAME, ComposeFileStatus, ComposeSandbox

logger = logging.getLogger(__name__)


@click.command(
    "goal",
    short_help="Run the Algorand goal CLI against the AlgoKit LocalNet.",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.option(
    "--console",
    is_flag=True,
    help="Open a Bash console so you can execute multiple goal commands and/or interact with a filesystem.",
    default=False,
)
@click.argument("goal_args", nargs=-1, type=click.UNPROCESSED)
def goal_command(*, console: bool, goal_args: list[str]) -> None:
    """
    Run the Algorand goal CLI against the AlgoKit LocalNet.

    Look at https://developer.algorand.org/docs/clis/goal/goal/ for more information.
    """
    goal_args = list(goal_args)
    try:
        proc.run(["docker", "version"], bad_return_code_error_message="Docker engine isn't running; please start it.")
    except OSError as ex:
        # an IOError (such as PermissionError or FileNotFoundError) will only occur if "docker"
        # isn't an executable in the user's path, which means docker isn't installed
        raise click.ClickException(
            "Docker not found; please install Docker and add to path.\n"
            "See https://docs.docker.com/get-docker/ for more information."
        ) from ex

    sandbox = ComposeSandbox.from_environment()
    if sandbox is None:
        sandbox = ComposeSandbox()

    if sandbox.name != DEFAULT_NAME:
        logger.info("A named LocalNet is running, goal command will be executed against the named LocalNet")

    volume_mount_path_local = get_volume_mount_path_local(directory_name=sandbox.name)
    volume_mount_path_docker = get_volume_mount_path_docker()

    compose_file_status = sandbox.compose_file_status()
    if compose_file_status is not ComposeFileStatus.UP_TO_DATE and sandbox.name == DEFAULT_NAME:
        raise click.ClickException("LocalNet definition is out of date; please run `algokit localnet reset` first!")
    ps_result = sandbox.ps("algod")
    match ps_result:
        case [{"State": "running"}]:
            pass
        case _:
            logger.info("LocalNet isn't running")
            sandbox.up()

    if console:
        if goal_args:
            logger.warning("--console opens an interactive shell, remaining arguments are being ignored")
        logger.info("Opening Bash console on the algod node; execute `exit` to return to original console")
        result = proc.run_interactive(f"docker exec -it -w /root algokit_{sandbox.name}_algod bash".split())
    else:
        cmd = f"docker exec --interactive --workdir /root algokit_{sandbox.name}_algod goal".split()
        input_files, output_files, goal_args = preprocess_command_args(
            goal_args, volume_mount_path_local, volume_mount_path_docker
        )
        cmd = cmd + goal_args
        result = proc.run(
            cmd,
            stdout_log_level=logging.INFO,
            prefix_process=False,
            pass_stdin=True,
        )
        post_process(input_files, output_files, volume_mount_path_local)

    if result.exit_code != 0:
        raise click.exceptions.Exit(result.exit_code)
