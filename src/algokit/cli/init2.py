import logging
import shutil
import subprocess
from pathlib import Path
from typing import NoReturn

import click

from algokit.cli.app.project_wizard import ProjectWizard
from algokit.core.init import is_valid_project_dir_name

logger = logging.getLogger(__name__)


def _fail_and_bail() -> NoReturn:
    """Exit the program with an error code"""
    logger.info("🛑 Bailing out... 👋")
    raise click.exceptions.Exit(code=1)


def _validate_dir_name(context: click.Context, param: click.Parameter, value: str | None) -> str | None:
    """Validate the provided directory name"""
    if value is not None and not is_valid_project_dir_name(value):
        raise click.BadParameter(
            "Invalid directory name. Ensure it's a mix of letters, numbers, dashes, "
            "periods, and/or underscores, and not already used.",
            context,
            param,
        )
    return value


@click.command("init2", short_help="Initializes a new project from a template.")
@click.option(
    "directory_name",
    "--name",
    "-n",
    type=str,
    help="Name of the project directory to create.",
    callback=_validate_dir_name,
)
def init2_command(
    *,
    directory_name: str | None,
) -> None:
    """
    Initializes a new project from a template.
    This should be run in the parent directory where you want the project folder created.
    """

    if not shutil.which("git"):
        raise click.ClickException(
            "Git not found; please install git and add to path.\n"
            "See https://github.com/git-guides/install-git for more information."
        )

    # Set up templates directory in .algokit folder
    templates_repo_url = "https://github.com/lempira/template-gallery-spike"
    algokit_dir = Path.home() / ".algokit"
    templates_dir = algokit_dir / "templates-gallery-spike"

    try:
        if not templates_dir.exists():
            # Clone the repository if it doesn't exist
            logger.info("Cloning templates repository...")
            algokit_dir.mkdir(exist_ok=True)
            subprocess.run(
                ["git", "clone", templates_repo_url, str(templates_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            # Pull latest changes if the repository exists
            logger.info("Updating templates repository...")
            subprocess.run(
                ["git", "-C", str(templates_dir), "pull"],
                check=True,
                capture_output=True,
                text=True,
            )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch templates: {e.stderr}")
        _fail_and_bail()

    # Launch cli app here
    app = ProjectWizard()
    app.run()
