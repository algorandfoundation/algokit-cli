import logging
import sys
from pathlib import Path

import click
import questionary
from algokit.core import proc
from copier import run_copy  # type: ignore

logger = logging.getLogger(__name__)


_blessed_templates = {
    "beaker-default": "gh:copier-org/autopretty",
}

_unofficial_template_warning = "<INSERT warning message about community / unofficial templates HERE>"


@click.command("init", short_help="Initializes a new project.")
@click.option("--name", type=str, help="Name of the directory / repository to create.")
@click.option(
    "--template",
    type=click.Choice(list(_blessed_templates.keys())),
    default=None,
    help="Name of an official template to use",
)
@click.option(
    "--template-url",
    type=str,
    default=None,
    help=(
        "URL to a git repo with a custom project template. "
        "Can use shorthand of gh: instead of github.com and gl: instead of gitlab.com"
    ),
)
@click.option("--git/--no-git", default=None, help="Initialise git repository in directory after creation.")
def init_command(name: str | None, template: str | None, template_url: str | None, git: bool | None) -> None:
    """Initializes a new project from a template."""

    if template and template_url:
        raise click.ClickException("Cannot specify both --template and --template-url")

    project_path, directory_pre_existing = _get_project_path(name)

    if template:
        template_url = _blessed_templates[template]
    elif template_url:
        logger.warning(_unofficial_template_warning)
        if not questionary.confirm("Continue anyway?", default=False).ask():
            logger.info("Bailing out...\n( o_o) /シ")
            sys.exit(1)
    else:
        template_url = _get_template_url()
    logger.debug(f"Attempting to initialise project in {project_path} from template {template_url}")

    run_copy(template_url, project_path)
    logger.debug("Project initialisation complete")
    if git and not directory_pre_existing:
        _git_init(
            project_path, default_commit_message=f"Project initialised with AlgoKit CLI using template: {template}"
        )


def _get_project_path(name: str | None = None) -> tuple[Path, bool]:
    if name is None:
        name = questionary.text(
            "Name of directory to create the project in: ",
            validate=lambda text: True if len(text) > 0 else "Please enter a value",
        ).ask()
    project_path = Path.cwd() / name
    # TODO: move some/all of below validation into questionary
    if directory_pre_existing := project_path.exists():
        if not project_path.is_dir():
            logger.warning("File with same name already exists in current directory, please enter a different name")
            return _get_project_path()
        logger.warning(
            "Re-using existing directory, this is not recommended because if project generation fails, "
            "then we can't automatically cleanup."
        )
        if not questionary.confirm("Continue anyway?", default=False).ask():
            return _get_project_path()
    return project_path, directory_pre_existing


def _get_template_url() -> str:
    template_choices: dict[str, str | None] = {**_blessed_templates, "custom url": None}
    choice_name = questionary.select("Select a project template: ", choices=list(template_choices.keys())).ask()
    template_url = template_choices[choice_name]
    if template_url:
        return template_url
    logger.warning(_unofficial_template_warning)
    template_url = questionary.text(
        (
            "Enter a custom project URL, or hit enter to go back to official template selection.\n"
            "Note that you can use gh: as a shorthand for github.com and likewise gl: for gitlab.com"
        )
    ).ask()
    if template_url and template_url.strip():
        return template_url
    else:
        # re-prompt
        return _get_template_url()


def _git_init(project_path: Path, default_commit_message: str) -> None:
    try:
        git_init_result = proc.run(["git", "init"], cwd=project_path)
    except FileNotFoundError:
        logger.warning("git command wasn't found on your PATH, skipping repository initialisation")
        return
    else:
        if git_init_result.exit_code != 0:
            logger.warning("Failed to initialise git repository")
            return
    git_add_result = proc.run(["git", "add", "--all"], cwd=project_path, stdout_log_level=logging.INFO)
    if git_add_result.exit_code != 0:
        logger.warning("Failed to add generated project files")
        return
    try:
        commit_message: str = click.prompt(
            "Ready to commit initial changes. To skip committing, ctrl-c now. Otherwise, you can modify ",
            default=default_commit_message,
            type=str,
        )
    except click.Abort:
        logger.info("Skipping initial commit")
        return
    git_commit_result = proc.run(
        ["git", "commit", "-m", commit_message], cwd=project_path, stdout_log_level=logging.INFO
    )
    if git_commit_result.exit_code != 0:
        logger.warning("Initial commit failed")
        return
