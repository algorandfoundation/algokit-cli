import enum
import logging

import click
import questionary

from algokit.core.conf import get_app_config_dir

logger = logging.getLogger(__name__)

CONTAINER_ENGINE_CONFIG_FILE = get_app_config_dir() / "active-container-engine"


class ContainerEngine(str, enum.Enum):
    DOCKER = "docker"
    PODMAN = "podman"

    def __str__(self) -> str:
        return self.value


def get_container_engine() -> str:
    if CONTAINER_ENGINE_CONFIG_FILE.exists():
        return CONTAINER_ENGINE_CONFIG_FILE.read_text().strip()
    return str(ContainerEngine.DOCKER)


def save_container_engine(engine: str) -> None:
    if engine not in ContainerEngine:
        raise ValueError(f"Invalid container engine: {engine}")
    CONTAINER_ENGINE_CONFIG_FILE.write_text(engine)


@click.command("container-engine", short_help="Configure the container engine for AlgoKit LocalNet.")
@click.argument("engine", required=False, type=click.Choice(["docker", "podman"]))
@click.option(
    "--force",
    "-f",
    is_flag=True,
    required=False,
    default=False,
    type=click.BOOL,
    help=("Skip confirmation prompts. " "Defaults to 'yes' to all prompts."),
)
def container_engine_configuration_command(*, engine: str | None, force: bool) -> None:
    """Set the default container engine for use by AlgoKit CLI to run LocalNet images."""
    from algokit.core.sandbox import ComposeSandbox

    if engine is None:
        current_engine = get_container_engine()
        choices = [
            f"Docker {'(Active)' if current_engine == ContainerEngine.DOCKER else ''}".strip(),
            f"Podman {'(Active)' if current_engine == ContainerEngine.PODMAN else ''}".strip(),
        ]
        engine = questionary.select("Which container engine do you prefer?", choices=choices).ask()
        if engine is None:
            raise click.ClickException("No valid container engine selected. Aborting...")
        engine = engine.split()[0].lower()

    sandbox = ComposeSandbox.from_environment()
    has_active_instance = sandbox is not None and (
        force
        or click.confirm(
            f"Detected active localnet instance, would you like to restart it with '{engine}'?",
            default=True,
        )
    )
    if sandbox and has_active_instance:
        sandbox.down()
        save_container_engine(engine)
        sandbox.write_compose_file()
        sandbox.up()
    else:
        save_container_engine(engine)

    logger.info(f"Container engine set to `{engine}`")
