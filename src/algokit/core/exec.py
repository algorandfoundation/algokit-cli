import logging
import subprocess
from pathlib import Path

import click

logger = logging.getLogger(__name__)


def run(
    command: str,
    working_directory: Path | None = None,
    suppress_output: bool = False,
    throw_on_error: str | None = None,
):
    """Runs the given command by spawing a sub process in the given working directory (or cwd if unspecified)"""
    if not suppress_output:
        logger.debug(f"Running '{command}' in '{working_directory or Path.cwd()}'")
    result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory)
    if not suppress_output and result.stdout.decode("utf-8").strip().__len__() > 0:
        logger.debug(result.stdout.decode("utf-8"))

    if throw_on_error is not None and result.returncode != 0:
        logger.error(result.stderr.decode("utf-8"))
        raise click.ClickException(throw_on_error)

    return result
