import dataclasses
import logging
import re
import traceback
from collections.abc import Callable
from shutil import which

from algokit.core import proc
from algokit.core.utils import is_minimum_version

logger = logging.getLogger(__name__)


def _get_version_or_first_non_blank_line(output: str) -> str:
    match = re.search(r"\d+\.\d+\.\d+", output)
    if match:
        return match.group(0)
    lines = output.splitlines()
    non_blank_lines = filter(None, (ln.strip() for ln in lines))
    # return first non-blank line or empty string if all blank
    return next(non_blank_lines, "")


@dataclasses.dataclass
class DoctorResult:
    ok: bool
    output: str
    extra_help: list[str] | None = None


def format_exception_only(ex: Exception) -> list[str]:
    return [ln.rstrip("\n") for ln in traceback.format_exception_only(type(ex), ex)]


def check_dependency(
    cmd: list[str],
    *,
    missing_help: list[str] | None = None,
    successful_output_parser: Callable[[str], str] = _get_version_or_first_non_blank_line,
    include_location: bool = False,
    minimum_version: str | None = None,
    minimum_version_help: list[str] | None = None,
) -> DoctorResult:
    """Check a dependency by running a command.

    :param cmd: command to run
    :param missing_help: Optional additional text to display if command is not found
    :param successful_output_parser: Optional method to trim down or parse the output of the version command.
            If not specified, an attempt will be made to extra a major.minor.patch value,
            otherwise the first non-blank line will be used
    :param include_location: Include the path to `command` in the output?`
    :param minimum_version: Optional value to check minimum version against.
    :param minimum_version_help: Custom help output if minimum version not met.
    """
    try:
        proc_result = proc.run(cmd)
    except FileNotFoundError:
        logger.debug("Command not found", exc_info=True)
        return DoctorResult(ok=False, output="Command not found!", extra_help=missing_help)
    except PermissionError:
        logger.debug("Permission denied running command", exc_info=True)
        return DoctorResult(ok=False, output="Permission denied attempting to run command")
    except Exception as ex:
        logger.debug(f"Unexpected exception running command: {ex}", exc_info=True)
        return DoctorResult(
            ok=False,
            output="Unexpected error running command",
            extra_help=format_exception_only(ex),
        )

    try:
        if proc_result.exit_code != 0:
            return DoctorResult(
                ok=False,
                output=f"Command exited with code: {proc_result.exit_code}",
                extra_help=proc_result.output.splitlines(),
            )
        output = version_output = successful_output_parser(proc_result.output)
        if include_location:
            location = which(cmd[0])
            output += f" (location: {location})"

    except Exception as ex:
        logger.debug(f"Unexpected error checking dependency: {ex}", exc_info=True)
        return DoctorResult(
            ok=False,
            output="Unexpected error checking dependency",
            extra_help=format_exception_only(ex),
        )
    if minimum_version is not None:
        try:
            match = re.search(r"^\d+\.\d+\.\d+", output)
            if not match:
                raise Exception("Unable to parse version number")
            version_ok = is_minimum_version(match.group(0), minimum_version)
        except Exception as ex:
            logger.debug(f"Unexpected error parsing version: {ex}", exc_info=True)
            return DoctorResult(
                ok=False,
                output=output,
                extra_help=[
                    f'Failed to parse version from: "{version_output}"',
                    f"Error: {ex}",
                    f"Unable to check against minimum version of {minimum_version}",
                ],
            )
        if not version_ok:
            return DoctorResult(
                ok=False,
                output=output,
                extra_help=(minimum_version_help or [f"Minimum version required: {minimum_version}"]),
            )
    return DoctorResult(ok=True, output=output)
