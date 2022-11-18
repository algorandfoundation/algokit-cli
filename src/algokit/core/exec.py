import dataclasses
import logging
import subprocess
from pathlib import Path

import click

from algokit.core.log_handlers import EXTRA_EXCLUDE_FROM_CONSOLE, EXTRA_EXCLUDE_FROM_LOGFILE

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class RunResult:
    command: str
    exit_code: int
    output: str


def run(
    command: list[str],
    cwd: Path | None = None,
    timeout: int | float | None = None,
    env: dict[str, str] | None = None,
    bad_return_code_error_message: str | None = None,
) -> RunResult:
    """Wraps subprocess.run() to add: logging and unicode I/O capture

    Note that not all options or usage scenarios here are covered, just some common use cases
    """
    command_str = " ".join(command)
    logger.debug(f"Running '{command_str}' in '{cwd or Path.cwd()}'")

    # note: we don't pass check parameter through, so we can log the result regardless of success/failure being checked
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,  # capture stdout
        stderr=subprocess.STDOUT,  # redirect stderr to stdout, so they're interleaved in the correct ordering
        text=True,  # make all I/O in unicode/text
        cwd=cwd,
        timeout=timeout,
        env=env,
    )
    # a bit gnarly, but log the full results to the log file (for debugging / error reporting),
    # and just show process output in verbose mode to console
    logger.debug(
        str(result),
        extra=EXTRA_EXCLUDE_FROM_CONSOLE,
    )
    logger.debug(
        result.stdout,
        extra=EXTRA_EXCLUDE_FROM_LOGFILE,
    )
    if result.returncode != 0 and bad_return_code_error_message:
        raise click.ClickException(bad_return_code_error_message)
    return RunResult(command=command_str, exit_code=result.returncode, output=result.stdout)
