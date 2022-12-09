import logging
import sys

import click
from algokit.core import proc

logger = logging.getLogger(__name__)


@click.group("bootstrap", short_help="Bootstrap AlgoKit project dependencies.")
def bootstrap_group() -> None:
    pass


@bootstrap_group.command("poetry", short_help="Bootstrap Python Poetry and install in the current working directory.")
@click.option(
    "--ok-exit-code",
    default=False,
    help="Always return a 0 exit code; useful when calling as task from a Copier template to avoid template delete.",
    is_flag=True,
)
def poetry(*, ok_exit_code: bool) -> None:
    try:
        python = sys.executable
        try:
            proc.run(["poetry", "-V"])
        except IOError:
            # An IOError (such as PermissionError or FileNotFoundError) will only occur if "poetry"
            # isn't an executable in the user's path, which means poetry isn't installed
            try:
                proc.run(["pipx", "--version"])
            except IOError:
                # An IOError (such as PermissionError or FileNotFoundError) will only occur if "pipx"
                # isn't an executable in the user's path, which means pipx isn't installed

                proc.run(
                    [python, "-m", "pip", "install", "--user", "pipx"],
                    bad_return_code_error_message="Unable to install pipx; please install"
                    + " pipx manually via https://pypa.github.io/pipx/ and try `algokit bootstrap poetry` again.",
                )

                proc.run(
                    [python, "-m", "pipx", "ensurepath"],
                    bad_return_code_error_message="Unable to update pipx install path to global path;"
                    + " please set the path manually and try `algokit bootstrap poetry` again.",
                )

            proc.run(
                ["pipx", "install", "poetry"],
                bad_return_code_error_message="Unable to install poetry via pipx; please install poetry"
                + " manually via https://python-poetry.org/docs/ and try `algokit bootstrap poetry` again.",
            )

        logger.info("Installing Python dependencies and setting up Python virtual environment via Poetry")
        proc.run(["poetry", "install"], stdout_log_level=logging.INFO)

    except Exception as ex:
        logger.error(ex)
        if ok_exit_code:
            logger.error("Error bootstrapping poetry; try running `poetry install` manually.")
        else:
            raise click.ClickException("Error bootstrapping poetry; try running `poetry install` manually.") from ex
