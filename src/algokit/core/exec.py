import dataclasses
import logging
import subprocess
from pathlib import Path

import click

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class RunResult:
    command: str
    exit_code: int
    output: str


def run(
    command: list[str],
    cwd: Path | None = None,
    check: bool = True,
    timeout: int | float | None = None,
    env: dict[str, str] | None = None,
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
    logger.debug(f"Execution of '{command_str}' completed with code {result.returncode}, output = \n{result.stdout}")
    if result.returncode != 0:
        if check:
            raise click.ClickException(error_message or f"Command failed: '{command_str}'")
    return RunResult(command=command_str, exit_code=result.returncode, output=result.stdout)
