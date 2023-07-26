import dataclasses
import logging
from pathlib import Path

import click

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config

logger = logging.getLogger(__name__)


@dataclasses.dataclass(kw_only=True)
class Generator:
    name: str | None = None
    description: str | None = None
    path: str | None = None


def _format_generator_name(name: str) -> str:
    """
    Format the generator name to be used as a command name.
    :param name: Generator name.
    :return: Formatted generator name.
    """

    return name.strip().replace(" ", "-").replace("_", "-")


def _run_generator(answers: dict, path: Path) -> None:
    """
    Run the generator with the given answers and path.
    :param answers: Answers to pass to the generator.
    :param path: Path to the generator.
    """

    # copier is lazy imported for two reasons
    # 1. it is slow to import on first execution after installing
    # 2. the import fails if git is not installed (which we check above)
    from copier.main import Worker  # type: ignore[import]

    cwd = Path.cwd()
    with Worker(
        src_path=str(path),
        dst_path=cwd,
        data=answers,
        quiet=True,
    ) as copier_worker:
        logger.debug(f"Running generator in {copier_worker.src_path}")
        copier_worker.run_copy()


def _load_generators(project_dir: Path) -> list[Generator]:
    """
    Load the generators for the given project from .algokit.toml file.
    :param project_dir: Project directory path.
    :return: Generators.
    """
    # Load and parse the TOML configuration file
    config = get_algokit_config(project_dir)
    generators: list[Generator] = []

    if not config:
        return generators

    generators_table = config.get("generate", {})

    if not isinstance(generators_table, dict):
        raise click.ClickException(f"Bad data for [generators] key in '{ALGOKIT_CONFIG}'")

    for name, generators_config in generators_table.items():
        match generators_config:
            case dict():
                if not generators_config.get("path"):
                    logger.warning(f"Missing path for generator '{name}' in '{ALGOKIT_CONFIG}', skipping")
                    continue
                if not Path.exists(Path(generators_config.get("path", ""))):
                    logger.warning(
                        f"Path '{generators_config.get('path')}' for generator '{name}' does not exist, skipping"
                    )
                    continue

                generator = Generator(
                    name=_format_generator_name(name),
                    description=generators_config.get("description"),
                    path=generators_config.get("path"),
                )
                generators.append(generator)

    return generators


def load_custom_generate_commands(project_dir: Path) -> list[click.Command]:
    generators = _load_generators(project_dir)
    commands = []

    for generator in generators:
        # Set the generator name and description as a new command
        command = click.command(name=generator.name, help=generator.description)(_run_generator)

        # Add the options to the command to allow passing answers and custom path (optional)
        command = click.option(
            "answers",
            "--answer",
            "-a",
            multiple=True,
            help="Answers key/value pairs to pass to the template.",
            nargs=2,
            default=[],
            metavar="<key> <value>",
        )(command)
        command = click.option(
            "path",
            "--path",
            "-p",
            help=f"Path to {generator.name} generator. (Default: {generator.description})",
            type=click.Path(exists=True),
            default=generator.path,
        )(command)
        commands.append(command)

    return commands
