import functools
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from types import TracebackType
from typing import Any, Callable, ParamSpec, TypeVar

import click
from click.globals import resolve_color_default

from .conf import get_app_state_dir

__all__ = [
    "initialise_logging",
    "output_options",
    "uncaught_exception_logging_handler",
    "EXTRA_EXCLUDE_FROM_CONSOLE",
    "EXTRA_EXCLUDE_FROM_LOGFILE",
    "get_colour_pref_from_args",
]


class ClickHandler(logging.Handler):
    """Handle console output with click.echo(...)

    Slightly special in that this class acts as both a sink and an additional formatter,
    but they're kind of intertwined for our use case of actually displaying things to the user.
    """

    styles: dict[str, dict[str, Any]] = {
        "critical": {"fg": "red", "bold": True},
        "error": {"fg": "red"},
        "warning": {"fg": "yellow"},
        "debug": {"fg": "cyan"},
    }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            if level in self.styles:
                # if user hasn't disabled colors/styling, just use that
                if resolve_color_default() is not False:
                    level_style = self.styles[level]
                    msg = click.style(msg, **level_style)
                # otherwise, prefix the level name
                else:
                    msg = f"{level.upper()}: {msg}"
            click.echo(msg)
        except Exception:
            self.handleError(record)


class NoExceptionFormatter(logging.Formatter):
    """Prevent automatically displaying exception/traceback info.
    (without interfering with other formatters that might later want to add such information)
    """

    def formatException(self, *args: Any) -> str:  # noqa: N802
        return ""

    def formatStack(self, *args: Any) -> str:  # noqa: N802
        return ""


CONSOLE_LOG_HANDLER_NAME = "console_log_handler"

EXCLUDE_FROM_KEY = "exclude_from"
EXCLUDE_FROM_CONSOLE_VALUE = "console"
EXCLUDE_FROM_LOGFILE_VALUE = "logfile"

EXTRA_EXCLUDE_FROM_CONSOLE = {EXCLUDE_FROM_KEY: EXCLUDE_FROM_CONSOLE_VALUE}
EXTRA_EXCLUDE_FROM_LOGFILE = {EXCLUDE_FROM_KEY: EXCLUDE_FROM_LOGFILE_VALUE}


class ManualExclusionFilter(logging.Filter):
    def __init__(self, exclude_value: str):
        super().__init__()
        self.exclude_value = exclude_value

    def filter(self, record: logging.LogRecord) -> bool:
        return getattr(record, EXCLUDE_FROM_KEY, None) != self.exclude_value


# HACK: due to there being no support for "global flags" in click (see: https://github.com/pallets/click/issues/66),
#       we handle these flags specially. All groups/commands should have the @output_options decorator below added,
#       so that the help doc shows these as correctly being applicable anywhere, but in order to prevent user
#       confusion when specifying before or after a command gives different results, and similarly for colour options
#       (e.g. if you pass --no-color as the last flag on the command line, it's very surprising if colour shows up
#       in some of the output, which it can if there's output in parent groups)
_VERBOSE_FLAGS = ["--verbose", "-v"]


def initialise_logging() -> None:
    console_log_handler = ClickHandler()
    if set(_VERBOSE_FLAGS).intersection(sys.argv):
        console_log_level = logging.DEBUG
    else:
        console_log_level = logging.INFO
    console_log_handler.setLevel(console_log_level)
    console_log_handler.name = CONSOLE_LOG_HANDLER_NAME
    console_log_handler.formatter = NoExceptionFormatter()
    console_log_handler.addFilter(ManualExclusionFilter(exclude_value=EXCLUDE_FROM_CONSOLE_VALUE))

    file_log_handler = RotatingFileHandler(
        filename=get_app_state_dir() / "cli.log",
        maxBytes=1 * 1024 * 1024,
        backupCount=5,
    )
    file_log_handler.setLevel(logging.DEBUG)
    file_log_handler.formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )
    file_log_handler.addFilter(ManualExclusionFilter(exclude_value=EXCLUDE_FROM_LOGFILE_VALUE))

    logging.basicConfig(level=logging.DEBUG, handlers=[console_log_handler, file_log_handler], force=True)


def uncaught_exception_logging_handler(
    exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None
) -> None:
    """Function to be used as sys.excepthook, which logs uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        # don't log ctrl-c or equivalents
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    else:
        logging.critical(f"Unhandled {exc_type.__name__}: {exc_value}", exc_info=(exc_type, exc_value, exc_traceback))


_ENABLE_COLOR_FLAG = "--color"
_DISABLE_COLOR_FLAG = "--no-color"


T = TypeVar("T")
P = ParamSpec("P")


def output_options(func: Callable[P, T]) -> Callable[P, T]:
    # if you're wondering why these options do nothing, please see the HACK comment above,
    # where the names are declared
    @click.option(
        *_VERBOSE_FLAGS,
        is_flag=True,
        expose_value=False,
        help="Enable logging of DEBUG messages to the console",
    )
    @click.option(
        f"{_ENABLE_COLOR_FLAG}/{_DISABLE_COLOR_FLAG}",
        default=None,
        expose_value=False,
        help="Force enable or disable of console output styling",
    )
    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        return func(*args, **kwargs)

    return wrapped


def get_colour_pref_from_args(argv: list[str]) -> bool | None:
    # search in reverse, last specified wins.
    # see HACK note above for why this function exists
    for arg in reversed(argv):
        if arg == _ENABLE_COLOR_FLAG:
            return True
        if arg == _DISABLE_COLOR_FLAG:
            return False
    # support NO_COLOR (ref: https://no-color.org) env var as default value,
    if os.getenv("NO_COLOR"):
        return False
    return None
