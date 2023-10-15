import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from types import TracebackType
from typing import Any, ClassVar

import click
from click.globals import resolve_color_default

from .conf import get_app_state_dir

__all__ = [
    "initialise_logging",
    "color_option",
    "verbose_option",
    "uncaught_exception_logging_handler",
    "EXTRA_EXCLUDE_FROM_CONSOLE",
    "EXTRA_EXCLUDE_FROM_LOGFILE",
]


class ClickHandler(logging.Handler):
    """Handle console output with click.echo(...)

    Slightly special in that this class acts as both a sink and an additional formatter,
    but they're kind of intertwined for our use case of actually displaying things to the user.
    """

    styles: ClassVar[dict[str, dict[str, Any]]] = {
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

    def formatException(self, *_args: Any) -> str:  # noqa: N802
        return ""

    def formatStack(self, *_args: Any) -> str:  # noqa: N802
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

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        return getattr(record, EXCLUDE_FROM_KEY, None) != self.exclude_value


def initialise_logging() -> None:
    console_log_handler = ClickHandler()
    # default to INFO, this case be upgraded later based on -v flag
    console_log_handler.setLevel(logging.INFO)
    console_log_handler.name = CONSOLE_LOG_HANDLER_NAME
    console_log_handler.formatter = NoExceptionFormatter()
    console_log_handler.addFilter(ManualExclusionFilter(exclude_value=EXCLUDE_FROM_CONSOLE_VALUE))

    file_log_handler = RotatingFileHandler(
        filename=get_app_state_dir() / "cli.log",
        maxBytes=1 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
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


def _set_verbose(_ctx: click.Context, _param: click.Option, value: bool) -> None:  # noqa: FBT001
    if value:
        for handler in logging.getLogger().handlers:
            if handler.name == CONSOLE_LOG_HANDLER_NAME:
                handler.setLevel(logging.DEBUG)
                return
        raise RuntimeError(f"Couldn't locate required logger named {CONSOLE_LOG_HANDLER_NAME}")


def _set_force_styles_to(ctx: click.Context, _param: click.Option, value: bool | None) -> None:
    if value is not None:
        ctx.color = value


verbose_option = click.option(
    "--verbose",
    "-v",
    is_flag=True,
    callback=_set_verbose,
    expose_value=False,
    help="Enable logging of DEBUG messages to the console.",
)

color_option = click.option(
    "--color/--no-color",
    # support NO_COLOR (ref: https://no-color.org) env var as default value,
    default=lambda: False if os.getenv("NO_COLOR") else None,
    callback=_set_force_styles_to,
    expose_value=False,
    help="Force enable or disable of console output styling.",
)
