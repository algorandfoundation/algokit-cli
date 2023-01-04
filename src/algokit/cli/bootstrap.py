import logging
from pathlib import Path

import click

from algokit.core.bootstrap import bootstrap_any_including_subdirs, bootstrap_env, bootstrap_npm, bootstrap_poetry
from algokit.core.questionary_extensions import _get_confirm_default_yes_prompt

logger = logging.getLogger(__name__)


@click.group("bootstrap", short_help="Bootstrap AlgoKit project dependencies.")
def bootstrap_group() -> None:
    pass


@bootstrap_group.command(
    "all", short_help="Bootstrap all aspects of the current directory and immediate sub directories by convention."
)
def bootstrap_all() -> None:
    cwd = Path.cwd()
    bootstrap_any_including_subdirs(cwd, _get_confirm_default_yes_prompt)
    logger.info(f"Finished bootstrapping {cwd}")


@bootstrap_group.command("env", short_help="Bootstrap .env file in the current working directory.")
def env() -> None:
    bootstrap_env(Path.cwd())


@bootstrap_group.command("poetry", short_help="Bootstrap Python Poetry and install in the current working directory.")
def poetry() -> None:
    bootstrap_poetry(Path.cwd(), _get_confirm_default_yes_prompt)


@bootstrap_group.command("npm", short_help="Bootstrap Node.js project in the current working directory.")
def npm() -> None:
    bootstrap_npm(Path.cwd())
