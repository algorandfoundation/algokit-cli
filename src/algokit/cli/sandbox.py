import logging
from subprocess import CalledProcessError

import click
from algokit.cli.goal import goal_command
from algokit.core import proc
from algokit.core.sandbox import (
    DOCKER_COMPOSE_MINIMUM_VERSION,
    ComposeFileStatus,
    ComposeSandbox,
    fetch_algod_status_data,
    fetch_indexer_status_data,
    get_docker_compose_version_string,
)
from algokit.core.utils import is_minimum_version

logger = logging.getLogger(__name__)


@click.group("sandbox", short_help="Manage the AlgoKit sandbox.")
def sandbox_group() -> None:
    try:
        compose_version_str = get_docker_compose_version_string() or ""
    except CalledProcessError as ex:
        raise click.ClickException(
            "Docker Compose not found; please install Docker Compose and add to path.\n"
            "See https://docs.docker.com/compose/install/ for more information."
        ) from ex
    except IOError as ex:
        # an IOError (such as PermissionError or FileNotFoundError) will only occur if "docker"
        # isn't an executable in the user's path, which means docker isn't installed
        raise click.ClickException(
            "Docker not found; please install Docker and add to path.\n"
            "See https://docs.docker.com/get-docker/ for more information."
        ) from ex
    else:
        try:
            compose_version_ok = is_minimum_version(compose_version_str, DOCKER_COMPOSE_MINIMUM_VERSION)
        except Exception:
            logger.warning(
                "Unable to extract docker compose version from output: \n"
                + compose_version_str
                + f"\nPlease ensure a minimum of compose v{DOCKER_COMPOSE_MINIMUM_VERSION} is used",
                exc_info=True,
            )
        else:
            if not compose_version_ok:
                raise click.ClickException(
                    f"Minimum docker compose version supported: v{DOCKER_COMPOSE_MINIMUM_VERSION}, "
                    f"installed = v{compose_version_str}\n"
                    "Please update your Docker install"
                )

    proc.run(["docker", "version"], bad_return_code_error_message="Docker engine isn't running; please start it.")


@sandbox_group.command("start", short_help="Start the AlgoKit Sandbox.")
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


@sandbox_group.command("stop", short_help="Stop the AlgoKit Sandbox.")
def stop_sandbox() -> None:
    sandbox = ComposeSandbox()
    compose_file_status = sandbox.compose_file_status()
    if compose_file_status is ComposeFileStatus.MISSING:
        logger.debug("Sandbox compose file does not exist yet; run `algokit sandbox start` to start the Sandbox")
    else:
        sandbox.stop()


@sandbox_group.command("reset", short_help="Reset the AlgoKit Sandbox.")
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


SERVICE_NAMES = ("algod", "indexer", "indexer-db")


@sandbox_group.command("status", short_help="Check the status of the AlgoKit Sandbox.")
def sandbox_status() -> None:
    sandbox = ComposeSandbox()
    ps = sandbox.ps()
    ps_by_name = {stats["Service"]: stats for stats in ps}
    # if any of the required containers does not exist (ie it's not just stopped but hasn't even been created),
    # then they will be missing from the output dictionary
    if set(SERVICE_NAMES) != ps_by_name.keys():
        raise click.ClickException("Sandbox has not been initialized yet, please run 'algokit sandbox start'")
    # initialise output dict by setting status
    output_by_name = {
        name: {"Status": "Running" if ps_by_name[name]["State"] == "running" else "Not running"}
        for name in SERVICE_NAMES
    }
    # fill out remaining output_by_name["algod"] values
    if output_by_name["algod"]["Status"] == "Running":
        output_by_name["algod"].update(fetch_algod_status_data(ps_by_name["algod"]))
    # fill out remaining output_by_name["indexer"] values
    if output_by_name["indexer"]["Status"] == "Running":
        output_by_name["indexer"].update(fetch_indexer_status_data(ps_by_name["indexer"]))

    # Print the status details
    for service_name, service_info in output_by_name.items():
        logger.info(click.style(f"# {service_name} status", bold=True))
        for key, value in service_info.items():
            logger.info(click.style(f"{key}:", bold=True) + f" {value}")

    # return non-zero if any container is not running
    if not all(item["Status"] == "Running" for item in output_by_name.values()):
        raise click.ClickException(
            "At least one container isn't running; execute `algokit sandbox start` to start the Sandbox"
        )


@sandbox_group.command(
    "console",
    short_help="Run the Algorand goal CLI against the AlgoKit Sandbox via a Bash console"
    + " so you can execute multiple goal commands and/or interact with a filesystem.",
)
@click.pass_context
def sandbox_console(context: click.Context) -> None:
    context.invoke(goal_command, console=True)
