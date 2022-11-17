import logging
import os
from logging.handlers import RotatingFileHandler

import click

from .conf import get_app_state_dir

__all__ = [
    "console_log_handler",
    "file_log_handler",
]


class ClickHandler(logging.Handler):
    """Handle console output with click.echo

    Slightly special in that this class acts as both a sink and a formatter,
    but they're kind of intertwined for our use case of actually displaying things to the user.
    """

    styles = {
        "critical": {"fg": "red", "bold": True},
        "error": {"fg": "red"},
        "warning": {"fg": "yellow"},
        "debug": {"fg": "cyan"},
    }

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

        # support NO_COLOR (ref: https://no-color.org),
        # otherwise if not set, don't force colors either on or off.
        # note that this could be modified by command line arguments,
        # this is just the initial default on app startup
        self.force_styles_to = False if os.getenv("NO_COLOR") else None

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            if level in self.styles:
                # if user hasn't disabled colors/styling, just use that
                if self.force_styles_to is not False:
                    level_style = self.styles[level]
                    msg = click.style(msg, **level_style)
                # otherwise, prefix the level name
                else:
                    msg = f"{level.upper()}: {msg}"
            click.echo(msg, color=self.force_styles_to)
        except Exception:
            self.handleError(record)


console_log_handler = ClickHandler()
console_log_handler.formatter = logging.Formatter("{message}", style="{")
# default to INFO, this case be upgraded later based on -v flag
console_log_handler.setLevel(logging.INFO)

file_log_handler = RotatingFileHandler(
    filename=get_app_state_dir() / "cli.log",
    maxBytes=1 * 1024 * 1024,
    backupCount=5,
)
file_log_handler.setLevel(logging.DEBUG)
file_log_handler.formatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
)
