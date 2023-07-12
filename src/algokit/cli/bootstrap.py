import logging
import os
from pathlib import Path

import click

from algokit.core.bootstrap import (
    bootstrap_any_including_subdirs,
    bootstrap_env,
    bootstrap_npm,
    bootstrap_poetry,
    project_minimum_algokit_version_check,
)

logger = logging.getLogger(__name__)


@click.option(
    "force", "--force", is_flag=True, default=False, help="Continue even if minimum AlgoKit version is not met"
)
@click.group(
    "bootstrap", short_help="Bootstrap local dependencies in an AlgoKit project; run from project root directory."
)
def bootstrap_group(*, force: bool) -> None:
    """
    Expedited initial setup for any developer by installing and configuring dependencies and other
    key development environment setup activities.
    """
    project_minimum_algokit_version_check(Path.cwd(), ignore_version_check_fail=force)


@bootstrap_group.command(
    "all", short_help="Runs all bootstrap sub-commands in the current directory and immediate sub directories."
)
@click.option(
    "--interactive/--non-interactive",
    " /--ci",  # this aliases --non-interactive to --ci
    default=lambda: "CI" not in os.environ,
    help="Enable/disable interactive prompts. If the CI environment variable is set, defaults to non-interactive",
)
def bootstrap_all(*, interactive: bool) -> None:
    cwd = Path.cwd()
    bootstrap_any_including_subdirs(cwd, ci_mode=not interactive)
    logger.info(f"Finished bootstrapping {cwd}")


@bootstrap_group.command(
    "env",
    short_help="Copies .env.template file to .env in the current working directory "
    "and prompts for any unspecified values.",
)
@click.option(
    "--interactive/--non-interactive",
    " /--ci",  # this aliases --non-interactive to --ci
    default=lambda: "CI" not in os.environ,
    help="Enable/disable interactive prompts. If the CI environment variable is set, defaults to non-interactive",
)
def env(*, interactive: bool) -> None:
    bootstrap_env(Path.cwd(), ci_mode=not interactive)


@bootstrap_group.command(
    "poetry",
    short_help="Installs Python Poetry (if not present) and runs `poetry install` in the "
    "current working directory to install Python dependencies.",
)
def poetry() -> None:
    bootstrap_poetry(Path.cwd())


@bootstrap_group.command(
    "npm", short_help="Runs `npm install` in the current working directory to install Node.js dependencies."
)
def npm() -> None:
    bootstrap_npm(Path.cwd())
