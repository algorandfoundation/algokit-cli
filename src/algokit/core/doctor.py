import dataclasses
import logging
import re
import traceback
from shutil import which

from algokit.core import proc
from algokit.core.utils import extract_version_triple, is_minimum_version

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class DoctorResult:
    ok: bool
    output: str
    extra_help: list[str] | None = None


def check_dependency(
    cmd: list[str],
    *,
    missing_help: list[str] | None = None,
    include_location: bool = False,
    minimum_version: str | None = None,
    minimum_version_help: list[str] | None = None,
) -> DoctorResult:
    """Check a dependency by running a command.

    :param cmd: command to run
    :param missing_help: Optional additional text to display if command is not found
    :param include_location: Include the path to `command` in the output?`
    :param minimum_version: Optional value to check minimum version against.
    :param minimum_version_help: Custom help output if minimum version not met.
    """
    result = _run_command(cmd, missing_help=missing_help)
    if result.ok:
        result = _process_version(
            run_output=result.output,
            minimum_version=minimum_version,
            minimum_version_help=minimum_version_help,
        )
        if include_location:
            try:
                location = which(cmd[0])
            except Exception as ex:
                logger.debug(f"Failed to locate {cmd[0]}: {ex}", exc_info=True)
                result.output += "f (location: unknown)"
            else:
                result.output += f" (location: {location})"
    return result


def _run_command(
    cmd: list[str],
    *,
    missing_help: list[str] | None = None,
) -> DoctorResult:
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
            extra_help=_format_exception_only(ex),
        )
    else:
        if proc_result.exit_code != 0:
            return DoctorResult(
                ok=False,
                output=f"Command exited with code: {proc_result.exit_code}",
                extra_help=proc_result.output.splitlines(),
            )
        return DoctorResult(ok=True, output=proc_result.output)


def _process_version(
    *,
    run_output: str,
    minimum_version: str | None,
    minimum_version_help: list[str] | None,
) -> DoctorResult:
    try:
        version_output = _get_version_or_first_non_blank_line(run_output)
    except Exception as ex:
        logger.debug(f"Unexpected error checking dependency: {ex}", exc_info=True)
        return DoctorResult(
            ok=False,
            output="Unexpected error checking dependency",
            extra_help=_format_exception_only(ex),
        )
    if minimum_version is not None:
        try:
            version_triple = extract_version_triple(version_output)
            version_ok = is_minimum_version(version_triple, minimum_version)
        except Exception as ex:
            logger.debug(f"Unexpected error parsing version: {ex}", exc_info=True)
            return DoctorResult(
                ok=False,
                output=version_output,
                extra_help=[
                    f'Failed to parse version from: "{version_output}"',
                    f"Error: {ex}",
                    f"Unable to check against minimum version of {minimum_version}",
                ],
            )
        if not version_ok:
            return DoctorResult(
                ok=False,
                output=version_output,
                extra_help=(minimum_version_help or [f"Minimum version required: {minimum_version}"]),
            )
    return DoctorResult(ok=True, output=version_output)


def _get_version_or_first_non_blank_line(output: str) -> str:
    match = re.search(r"\d+\.\d+\.\d+[^\s'\"(),]*", output)
    if match:
        return match.group()
    lines = output.splitlines()
    non_blank_lines = filter(None, (ln.strip() for ln in lines))
    # return first non-blank line or empty string if all blank
    return next(non_blank_lines, "")


def _format_exception_only(ex: Exception) -> list[str]:
    return [ln.rstrip("\n") for ln in traceback.format_exception_only(type(ex), ex)]
