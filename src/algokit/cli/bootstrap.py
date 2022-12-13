import logging
import sys
from pathlib import Path
from platform import system

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
        python = str(
            Path(sys.base_prefix) / "bin" / "python3"
            if system() != "Windows"
            else Path(sys.base_prefix) / "Scripts" / "python3.exe"
        )
        try:
            # Check we can access poetry via PATH
            proc.run(["poetry", "-V"])

            logger.info("Installing Python dependencies and setting up Python virtual environment via Poetry")
            proc.run(["poetry", "install"], stdout_log_level=logging.INFO)
        except IOError:
            # An IOError (such as PermissionError or FileNotFoundError) will only occur if "poetry"
            # isn't an executable in the user's path, which means poetry isn't installed
            try:
                # Check we can access pipx via PATH
                proc.run(["pipx", "--version"])

                # Install poetry via pipx
                proc.run(
                    ["pipx", "install", "poetry"],
                    bad_return_code_error_message="Unable to install poetry via pipx; please install poetry"
                    + " manually via https://python-poetry.org/docs/ and try `algokit bootstrap poetry` again.",
                )
            except IOError:
                # An IOError (such as PermissionError or FileNotFoundError) will only occur if "pipx"
                # isn't an executable in the user's path, try python -m pipx instead just in case

                # If pipx isn't found in global path or python -m pipx then bail out
                #   this is an exceptional circumstance since pipx should always be present with algokit
                #   since it's installed with brew / choco as a dependency, and otherwise is used to install algokit
                proc.run(
                    [python, "-m", "pipx", "--version"],
                    bad_return_code_error_message="Unable to find pipx install so that poetry can be installed; please"
                    + " install pipx via https://pypa.github.io/pipx/ and then try `algokit bootstrap poetry` again.",
                )

                # Install poetry via python -m pipx
                proc.run(
                    [python, "-m", "pipx", "install", "poetry"],
                    bad_return_code_error_message="Unable to install poetry via pipx; please install poetry"
                    + " manually via https://python-poetry.org/docs/ and try `algokit bootstrap poetry` again.",
                )

            try:
                logger.info("Installing Python dependencies and setting up Python virtual environment via Poetry")
                proc.run(["poetry", "install"], stdout_log_level=logging.INFO)
            except IOError as e:
                raise click.ClickException(
                    "Unable to access Poetry on PATH after installing it via pipx;"
                    + " check pipx installations are on your path by running pipx ensurepath"
                    + " and try `algokit bootstrap poetry` again."
                ) from e

    except Exception as ex:
        logger.error(ex)
        if ok_exit_code:
            logger.error("Error bootstrapping poetry; try running `poetry install` manually.")
        else:
            raise click.ClickException("Error bootstrapping poetry; try running `poetry install` manually.") from ex
