import dataclasses
import logging
import subprocess
from pathlib import Path
from subprocess import Popen

import click
from algokit.core.log_handlers import EXTRA_EXCLUDE_FROM_CONSOLE

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
    stdout_log_level: int = logging.DEBUG,
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
                    msg=click.style(f"{command[0]}:", bold=True) + f" {line.strip()}",
                )
    if exit_code == 0:  # type: ignore[unreachable]
        logger.debug(f"'{command_str}' completed successfully", extra=EXTRA_EXCLUDE_FROM_CONSOLE)
    else:
        logger.debug(f"'{command_str}' failed, exited with code = {exit_code}", extra=EXTRA_EXCLUDE_FROM_CONSOLE)
        if bad_return_code_error_message:
            raise click.ClickException(bad_return_code_error_message)
    output = "".join(lines)
    return RunResult(command=command_str, exit_code=exit_code, output=output)
