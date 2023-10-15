import dataclasses
import logging
import subprocess
import sys
from pathlib import Path
from subprocess import Popen
from subprocess import run as subprocess_run

import click

from algokit.core.log_handlers import EXTRA_EXCLUDE_FROM_CONSOLE

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class RunResult:
    command: str
    exit_code: int
    output: str


def run(  # noqa: PLR0913
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    bad_return_code_error_message: str | None = None,
    prefix_process: bool = True,
    stdout_log_level: int = logging.DEBUG,
    pass_stdin: bool = False,
) -> RunResult:
    """Wraps subprocess.Popen() similarly to subprocess.run() but adds: logging and streaming (unicode) I/O capture

    Note that not all options or usage scenarios here are covered, just some common use cases
    """
    command_str = " ".join(command)
    logger.debug(f"Running '{command_str}' in '{cwd or Path.cwd()}'")

    lines = []
    exit_code = None
    with Popen(
        command,
        stdout=subprocess.PIPE,  # capture stdout
        stderr=subprocess.STDOUT,  # redirect stderr to stdout, so they're interleaved in the correct ordering
        stdin=sys.stdin if pass_stdin else None,
        text=True,  # make all I/O in unicode/text
        cwd=cwd,
        env=env,
        bufsize=1,  # line buffering, works because text=True
    ) as proc:
        assert proc.stdout  # type narrowing
        while exit_code is None:
            line = proc.stdout.readline()
            if not line:
                # only poll if no output, so that we consume entire output stream
                exit_code = proc.poll()
            else:
                lines.append(line)
                logger.log(
                    level=stdout_log_level,
                    msg=(click.style(f"{command[0]}:", bold=True) if prefix_process else "") + f" {line.strip()}",
                )
    if exit_code == 0:  # type: ignore[unreachable]
        logger.debug(f"'{command_str}' completed successfully", extra=EXTRA_EXCLUDE_FROM_CONSOLE)
    else:
        logger.debug(f"'{command_str}' failed, exited with code = {exit_code}", extra=EXTRA_EXCLUDE_FROM_CONSOLE)
        if bad_return_code_error_message:
            raise click.ClickException(bad_return_code_error_message)
    output = "".join(lines)
    return RunResult(command=command_str, exit_code=exit_code, output=output)


def run_interactive(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    bad_return_code_error_message: str | None = None,
) -> RunResult:
    """Wraps subprocess.run() as an user interactive session and
        also adds logging of the command being executed, but not the output

    Note that not all options or usage scenarios here are covered, just some common use cases
    """
    command_str = " ".join(command)
    logger.debug(f"Running '{command_str}' in '{cwd or Path.cwd()}'")

    result = subprocess_run(command, cwd=cwd, env=env)

    if result.returncode == 0:
        logger.debug(f"'{command_str}' completed successfully", extra=EXTRA_EXCLUDE_FROM_CONSOLE)
    else:
        logger.debug(
            f"'{command_str}' failed, exited with code = {result.returncode}", extra=EXTRA_EXCLUDE_FROM_CONSOLE
        )
        if bad_return_code_error_message:
            raise click.ClickException(bad_return_code_error_message)
    return RunResult(command=command_str, exit_code=result.returncode, output="")
