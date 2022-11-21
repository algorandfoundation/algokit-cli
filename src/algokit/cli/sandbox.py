import logging

import click
from algokit.core import exec
from algokit.core.conf import get_app_config_dir
from algokit.core.sandbox import get_docker_compose_yml

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


@sandbox_group.command("start", short_help="Start the AlgoKit sandbox")
def start_sandbox() -> None:
    sandbox_dir = get_app_config_dir() / "sandbox"
    if not sandbox_dir.exists():
        logger.debug("Sandbox directory does not exist yet; creating it")
        sandbox_dir.mkdir()
    sandbox_compose_path = sandbox_dir / "docker-compose.yml"
    compose_content = get_docker_compose_yml()
    if not sandbox_compose_path.exists():
        logger.debug("Sandbox compose file does not exist yet; writing it out for the first time")
        sandbox_compose_path.write_text(compose_content)
    elif sandbox_compose_path.read_text() == compose_content:
        logger.debug("Sandbox compose file does not require updating")
    else:
        logger.warning("Sandbox definition is out of date; please run algokit sandbox reset")
    logger.info("Starting the AlgoKit sandbox now...")
    exec.run("docker compose up --detach --quiet-pull --wait".split(), cwd=sandbox_dir, stdout_log_level=logging.INFO)
    logger.info("Started; execute `algokit sandbox status` to check the status.")


@sandbox_group.command("reset", short_help="Reset the AlgoKit sandbox")
@click.option(
    "--pull/--no-pull",
    default=True,
    expose_value=True,
    help="Enable or disable pulling latest images from DockerHub",
)
@click.pass_context
def reset_sandbox(ctx: click.Context, *, pull: bool) -> None:
    sandbox_dir = get_app_config_dir() / "sandbox"
    sandbox_compose_path = sandbox_dir / "docker-compose.yml"
    if not sandbox_compose_path.exists():
        logger.debug("Existing Sandbox not found; creating from scratch...")
        ctx.invoke(start_sandbox)
    else:
        logger.info("Deleting any existing Sandbox...")
        exec.run("docker compose down".split(), cwd=sandbox_dir, stdout_log_level=logging.DEBUG)
        compose_content = get_docker_compose_yml()
        if sandbox_compose_path.read_text() != compose_content:
            logger.info("Sandbox definition is out of date; updating it to latest")
            sandbox_compose_path.write_text(compose_content)
        if pull:
            logger.info("Looking for latest Sandbox images from DockerHub...")
            exec.run(
                "docker compose pull --ignore-pull-failures --quiet".split(),
                cwd=sandbox_dir,
                stdout_log_level=logging.INFO,
            )
        logger.info("Starting the AlgoKit sandbox now...")
        exec.run(
            "docker compose up --detach --quiet-pull --wait".split(), cwd=sandbox_dir, stdout_log_level=logging.INFO
        )
        logger.info("Started; execute `algokit sandbox status` to check the status.")
