import dataclasses
import logging
import subprocess
from pathlib import Path
from subprocess import Popen

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
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    bad_return_code_error_message: str | None = None,
    stdout_as_info: bool = False,
) -> RunResult:
    """Wraps subprocess.Popen() to add: logging and unicode I/O capture

    Note that not all options or usage scenarios here are covered, just some common use cases
    """
    command_str = " ".join(command)
    logger.debug(f"Running '{command_str}' in '{cwd or Path.cwd()}'")

    # note: we don't pass check parameter through, so we can log the result regardless of success/failure being checked
    result = Popen(
        command,
        stdout=subprocess.PIPE,  # capture stdout
        stderr=subprocess.STDOUT,  # redirect stderr to stdout, so they're interleaved in the correct ordering
        text=True,  # make all I/O in unicode/text
        cwd=cwd,
        env=env,
    )

    # a bit gnarly, but log the full results to the log file (for debugging / error reporting),
    # and just show process output in verbose mode to console
    stdout = ""
    while True:
        output = result.stdout and result.stdout.readline()
        if output == "" and result.poll() is not None:
            break
        if output:
            if stdout_as_info:
                logger.info(
                    output.strip(),
                    extra=EXTRA_EXCLUDE_FROM_LOGFILE,
                )
            else:
                logger.debug(
                    output.strip(),
                    extra=EXTRA_EXCLUDE_FROM_LOGFILE,
                )
            stdout = stdout + output
    result.wait()
    logger.debug(
        stdout,
        extra=EXTRA_EXCLUDE_FROM_CONSOLE,
    )
    if result.returncode != 0 and bad_return_code_error_message:
        raise click.ClickException(bad_return_code_error_message)
    return RunResult(command=command_str, exit_code=result.returncode, output=stdout)
