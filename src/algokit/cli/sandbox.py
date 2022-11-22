import logging

import click
from algokit.core import exec
from algokit.core.sandbox import ComposeFileStatus, ComposeSandbox

logger = logging.getLogger(__name__)


@click.group("sandbox", short_help="Manage the AlgoKit sandbox")
def sandbox_group() -> None:
    try:
        exec.run(
            ["docker", "compose", "version"],
            bad_return_code_error_message=(
                "Docker Compose not found; please install Docker Compose and add to path.\n"
                "See https://docs.docker.com/compose/install/ for more information."
            ),
        )
    except IOError as ex:
        # an IOError (such as PermissionError or FileNotFoundError) will only occur if "docker"
        # isn't an executable in the user's path, which means docker isn't installed
        raise click.ClickException(
            "Docker not found; please install Docker and add to path.\n"
            "See https://docs.docker.com/get-docker/ for more information."
        ) from ex

    exec.run(["docker", "version"], bad_return_code_error_message="Docker engine isn't running; please start it.")


@sandbox_group.command("start", short_help="Start the AlgoKit Sandbox")
def start_sandbox() -> None:
    sandbox = ComposeSandbox()
    compose_file_status = sandbox.compose_file_status()
    if compose_file_status is ComposeFileStatus.MISSING:
        logger.debug("Sandbox compose file does not exist yet; writing it out for the first time")
        sandbox.write_compose_file()
    elif compose_file_status is ComposeFileStatus.UP_TO_DATE:
        logger.debug("Sandbox compose file does not require updating")
    else:
        logger.warning("Sandbox definition is out of date; please run algokit sandbox reset")
    sandbox.up()


@sandbox_group.command("reset", short_help="Reset the AlgoKit Sandbox")
@click.option(
    "--update/--no-update",
    default=True,
    help="Enable or disable updating to the latest available Sandbox version",
)
def reset_sandbox(update: bool) -> None:  # noqa: FBT001
    sandbox = ComposeSandbox()
    compose_file_status = sandbox.compose_file_status()
    if compose_file_status is ComposeFileStatus.MISSING:
        logger.debug("Existing Sandbox not found; creating from scratch...")
        sandbox.write_compose_file()
    else:
        sandbox.down()
        if compose_file_status is not ComposeFileStatus.UP_TO_DATE:
            logger.info("Sandbox definition is out of date; updating it to latest")
            sandbox.write_compose_file()
        if update:
            sandbox.pull()
    sandbox.up()
