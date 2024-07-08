import dataclasses
import logging
from pathlib import Path

import click

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config
from algokit.core.utils import get_python_paths

logger = logging.getLogger(__name__)


@dataclasses.dataclass(kw_only=True)
class Generator:
    name: str
    path: str
    description: str | None = None


def _format_generator_name(name: str) -> str:
    """
    Format the generator name to be used as a command name.
    :param name: Generator name.
    :return: Formatted generator name.
    """

    return name.strip().replace(" ", "-").replace("_", "-")


def run_generator(answers: dict, path: Path) -> None:
    """
    Run the custom generator with the given answers and path.
    :param answers: Answers to pass to the generator.
    :param path: Path to the generator.
    """

    # Below ensures that if the generator copier.yaml relies on python_path answer
    # it will be set to the system python path if available by algokit cli
    answers_dict = answers.copy()
    system_python_path = next(get_python_paths(), None)
    if system_python_path is not None:
        answers_dict.setdefault("python_path", system_python_path)
    else:
        answers_dict.setdefault("python_path", "no_system_python_available")

    # copier is lazy imported for two reasons
    # 1. it is slow to import on first execution after installing
    # 2. the import fails if git is not installed (which we check above)
    from copier.main import Worker

    cwd = Path.cwd()
    expected_answers_file = cwd / ".algokit" / ".copier-answers.yml"
    relative_answers_file = expected_answers_file.relative_to(cwd) if expected_answers_file.exists() else None

    with Worker(
        answers_file=relative_answers_file,
        src_path=str(path),
        dst_path=cwd,
        data=answers_dict,
        quiet=True,
        unsafe=True,
    ) as copier_worker:
        logger.debug(f"Running generator in {copier_worker.src_path}")
        copier_worker.run_copy()

    logger.info(f"Generator {path} executed successfully")


def load_generators(project_dir: Path) -> list[Generator]:
    """
    Load the generators for the given project from .algokit.toml file.
    :param project_dir: Project directory path.
    :return: Generators.
    """
    # Load and parse the TOML configuration file
    config = get_algokit_config(project_dir=project_dir)
    generators: list[Generator] = []

    if not config:
        return generators

    generators_table = config.get("generate", {})

    if not isinstance(generators_table, dict):
        raise click.ClickException(f"Bad data for [generators] key in '{ALGOKIT_CONFIG}'")

    for name, generators_config in generators_table.items():
        match generators_config:
            case {"path": str(path), **remaining}:
                if not Path(path).exists():
                    logger.warning(f"Path '{path}' for generator '{name}' does not exist, skipping")
                    continue

                description = remaining.get("description", None)
                generator = Generator(
                    name=_format_generator_name(name),
                    description=str(description) if description else None,
                    path=path,
                )
                generators.append(generator)

            case {"path": _}:
                logger.warning(f"Missing path for generator '{name}' in '{ALGOKIT_CONFIG}', skipping")

            case _:
                logger.debug(f'Invalid generator configuration key "{name}" of value "{generators_config}", skipping')

    return generators
