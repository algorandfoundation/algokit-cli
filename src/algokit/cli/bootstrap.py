import logging
import os
import shutil
import sys
from pathlib import Path
from platform import system

import click
from algokit.core import proc

logger = logging.getLogger(__name__)


def bootstrap_cwd(context: click.Context) -> None:
    current_dir = Path.cwd()
    env_path = current_dir / ".env.template"
    poetry_path = current_dir / "poetry.toml"
    pyproject_path = current_dir / "pyproject.toml"

    logger.debug(f"Checking {current_dir} for bootstrapping needs")

    if env_path.exists():
        logger.debug("Running `algokit bootstrap env`")
        context.invoke(
            env,
        )

    if poetry_path.exists() or (pyproject_path.exists() and "[tool.poetry]" in pyproject_path.read_text("utf-8")):
        logger.debug("Running `algokit bootstrap poetry`")
        context.invoke(poetry)


@click.group("bootstrap", short_help="Bootstrap AlgoKit project dependencies.")
def bootstrap_group() -> None:
    pass


@bootstrap_group.command(
    "all", short_help="Bootstrap all aspects of the current directory and immediate sub directories by convention."
)
@click.pass_context
def bootstrap_all(context: click.Context) -> None:
    base_path = Path.cwd()
    bootstrap_cwd(context)

    sub_dirs = base_path.glob("*/")
    for sub_dir in sub_dirs:
        if not sub_dir.is_dir():
            continue
        if sub_dir.name.lower() in [".venv", "node_modules", "__pycache__"]:
            logger.debug(f"Skipping {sub_dir}")
            continue
        os.chdir(sub_dir)
        try:
            bootstrap_cwd(context)
        finally:
            os.chdir(base_path)

    logger.info(f"Finished bootstrapping {base_path}")


@bootstrap_group.command("env", short_help="Bootstrap .env file in the current working directory.")
def env() -> None:
    base_path = Path.cwd()
    env_path = base_path / ".env"
    env_template_path = base_path / ".env.template"

    if env_path.exists():
        logger.info(".env already exists; skipping bootstrap of .env")
    else:
        logger.debug(f"{env_path} doesn't exist yet")
        if not env_template_path.exists():
            logger.info("No .env or .env.template file; nothing to do here, skipping bootstrap of .env")
        else:
            logger.debug(f"{env_template_path} exists")
            logger.info(f"Copying {env_template_path} to {env_path}")
            shutil.copyfile(env_template_path, env_path)


@bootstrap_group.command("poetry", short_help="Bootstrap Python Poetry and install in the current working directory.")
def poetry() -> None:
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
                + " check pipx installations are on your path by running `pipx ensurepath`"
                + " and try `algokit bootstrap poetry` again."
            ) from e
