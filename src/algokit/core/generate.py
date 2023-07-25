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


def load_generators(project_dir: Path) -> list[Generator]:
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
