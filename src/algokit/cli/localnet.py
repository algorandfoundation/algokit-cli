import logging

import click

from algokit.cli.explore import explore_command
from algokit.cli.goal import goal_command
from algokit.core import proc
from algokit.core.sandbox import (
    DEFAULT_NAME,
    DOCKER_COMPOSE_MINIMUM_VERSION,
    DOCKER_COMPOSE_VERSION_COMMAND,
    ComposeFileStatus,
    ComposeSandbox,
    fetch_algod_status_data,
    fetch_indexer_status_data,
)
from algokit.core.utils import extract_version_triple, is_minimum_version

logger = logging.getLogger(__name__)


@click.group("localnet", short_help="Manage the AlgoKit LocalNet.")
def localnet_group() -> None:
    try:
        compose_version_result = proc.run(DOCKER_COMPOSE_VERSION_COMMAND)
    except OSError as ex:
        # an IOError (such as PermissionError or FileNotFoundError) will only occur if "docker"
        # isn't an executable in the user's path, which means docker isn't installed
        raise click.ClickException(
            "Docker not found; please install Docker and add to path.\n"
            "See https://docs.docker.com/get-docker/ for more information."
        ) from ex
    if compose_version_result.exit_code != 0:
        raise click.ClickException(
            "Docker Compose not found; please install Docker Compose and add to path.\n"
            "See https://docs.docker.com/compose/install/ for more information."
        )

    try:
        compose_version_str = extract_version_triple(compose_version_result.output)
        compose_version_ok = is_minimum_version(compose_version_str, DOCKER_COMPOSE_MINIMUM_VERSION)
    except Exception:
        logger.warning(
            "Unable to extract docker compose version from output: \n"
            + compose_version_result.output
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


@localnet_group.command("start", short_help="Start the AlgoKit LocalNet.")
@click.option(
    "name",
    "--name",
    "-n",
    default=None,
    help="Specify a name for a custom LocalNet instance. "
    "AlgoKit will not manage the configuration of named LocalNet instances, "
    "allowing developers to configure it in any way they need.",
)
def start_localnet(name: str | None) -> None:
    sandbox = ComposeSandbox.from_environment()
    full_name = f"{DEFAULT_NAME}_{name}" if name is not None else DEFAULT_NAME
    if sandbox is not None and full_name != sandbox.name:
        logger.debug("LocalNet is already running.")
        if click.confirm("This will stop any running AlgoKit LocalNet instance. Are you sure?", default=True):
            sandbox.stop()
        else:
            raise click.ClickException("LocalNet is already running. Please stop it first")
    sandbox = ComposeSandbox() if name is None else ComposeSandbox(name)
    compose_file_status = sandbox.compose_file_status()
    sandbox.check_docker_compose_for_new_image_versions()
    if compose_file_status is ComposeFileStatus.MISSING:
        logger.debug("LocalNet compose file does not exist yet; writing it out for the first time")
        sandbox.write_compose_file()
        if name is not None:
            logger.info(
                f"The named LocalNet configuration has been created in {sandbox.directory}. \n"
                f"You can edit the configuration by changing those files. "
                f"Running `algokit localnet reset` will ensure the configuration is applied"
            )
    elif compose_file_status is ComposeFileStatus.UP_TO_DATE:
        logger.debug("LocalNet compose file does not require updating")
    elif compose_file_status is ComposeFileStatus.OUT_OF_DATE and name is None:
        logger.warning("LocalNet definition is out of date; please run `algokit localnet reset`")
    if name is not None:
        logger.info(
            "A named LocalNet is running, update checks are disabled. If you wish to synchronize with the latest "
            "version, run `algokit localnet reset --update`"
        )
    sandbox.up()


@localnet_group.command("stop", short_help="Stop the AlgoKit LocalNet.")
def stop_localnet() -> None:
    sandbox = ComposeSandbox.from_environment()
    if sandbox is not None:
        compose_file_status = sandbox.compose_file_status()
        if compose_file_status is not ComposeFileStatus.MISSING:
            sandbox.stop()
    else:
        logger.debug("LocalNet is not running; run `algokit localnet start` to start the AlgoKit LocalNet")


@localnet_group.command("reset", short_help="Reset the AlgoKit LocalNet.")
@click.option(
    "--update/--no-update",
    default=False,
    help="Enable or disable updating to the latest available LocalNet version, default: don't update",
)
def reset_localnet(*, update: bool) -> None:
    sandbox = ComposeSandbox.from_environment()
    if sandbox is None:
        sandbox = ComposeSandbox()
    compose_file_status = sandbox.compose_file_status()
    if compose_file_status is ComposeFileStatus.MISSING:
        logger.debug("Existing LocalNet not found; creating from scratch...")
        sandbox.write_compose_file()
    elif sandbox.name == DEFAULT_NAME:
        sandbox.down()
        if compose_file_status is not ComposeFileStatus.UP_TO_DATE:
            logger.info("LocalNet definition is out of date; updating it to latest")
            sandbox.write_compose_file()
        if update:
            sandbox.pull()
        else:
            sandbox.check_docker_compose_for_new_image_versions()
    elif update:
        if click.confirm(
            f"A named LocalNet is running, are you sure you want to reset the LocalNet configuration "
            f"in {sandbox.directory}?\nThis will stop the running LocalNet and overwrite any changes "
            "you've made to the configuration",
            default=True,
        ):
            sandbox.down()
            sandbox.write_compose_file()
            sandbox.pull()
        else:
            raise click.ClickException("LocalNet configuration has not been reset")
    else:
        sandbox.down()
    sandbox.up()


SERVICE_NAMES = ("algod", "conduit", "indexer-db", "indexer")


@localnet_group.command("status", short_help="Check the status of the AlgoKit LocalNet.")
def localnet_status() -> None:
    sandbox = ComposeSandbox.from_environment()
    if sandbox is None:
        sandbox = ComposeSandbox()
    ps = sandbox.ps()
    ps_by_name = {stats["Service"]: stats for stats in ps}
    # if any of the required containers does not exist (ie it's not just stopped but hasn't even been created),
    # then they will be missing from the output dictionary
    if set(SERVICE_NAMES) != ps_by_name.keys():
        raise click.ClickException("LocalNet has not been initialized yet, please run 'algokit localnet start'")
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
            "At least one container isn't running; execute `algokit localnet start` to start the LocalNet"
        )


@localnet_group.command(
    "console",
    short_help="Run the Algorand goal CLI against the AlgoKit LocalNet via a Bash console"
    " so you can execute multiple goal commands and/or interact with a filesystem.",
)
@click.pass_context
def localnet_console(context: click.Context) -> None:
    context.invoke(goal_command, console=True)


@localnet_group.command("explore", short_help="Explore the AlgoKit LocalNet using Dappflow")
@click.pass_context
def localnet_explore(context: click.Context) -> None:
    context.invoke(explore_command)


@localnet_group.command(
    "logs",
    short_help="See the output of the Docker containers",
)
@click.option(
    "--follow/-f",
    is_flag=True,
    help="Follow log output.",
    default=False,
)
@click.option(
    "--tail",
    default="all",
    help="Number of lines to show from the end of the logs for each container.",
    show_default=True,
)
@click.pass_context
def localnet_logs(ctx: click.Context, *, follow: bool, tail: str) -> None:
    sandbox = ComposeSandbox()
    sandbox.logs(follow=follow, no_color=ctx.color is False, tail=tail)
