import logging
import re
from pathlib import Path

try:
    from typing import Never  # type: ignore[attr-defined]
except ImportError:
    from typing import NoReturn as Never

# TODO: copier is typed, need to figure out how to force mypy to accept that or submit a PR
#       to their repo to include py.typed file
import click
import copier  # type: ignore
import copier.vcs  # type: ignore
import prompt_toolkit.document
import questionary
from algokit.core import proc
from algokit.core.log_handlers import EXTRA_EXCLUDE_FROM_CONSOLE

logger = logging.getLogger(__name__)


_blessed_templates = {
    "beaker-default": "gh:copier-org/autopretty",
    "simple": "gh:fastapi-mvc/copier-script",
}

_unofficial_template_warning = (
    "<INSERT warning message about community / unofficial templates & arbitrary code execution HERE>"
)


@click.command("init", short_help="Initializes a new project.")
@click.option("directory_name", "--name", type=str, help="Name of the directory / repository to create.")
@click.option(
    "template_name",
    "--template",
    type=click.Choice(list(_blessed_templates.keys())),
    default=None,
    help="Name of an official template to use",
)
@click.option(
    "--template-url",
    type=str,
    default=None,
    help="URL to a git repo with a custom project template.",
    metavar="URL",
)
@click.option("use_git", "--git/--no-git", default=None, help="Initialise git repository in directory after creation.")
@click.option(
    "answers",
    "--answer",
    "-a",
    multiple=True,
    help="Answers key/value pairs to pass to the template.",
    nargs=2,
    default=[],
    metavar="<key> <value>",
)
def init_command(
    directory_name: str | None,
    template_name: str | None,
    template_url: str | None,
    use_git: bool | None,
    answers: list[tuple[str, str]],
) -> None:
    """Initializes a new project from a template."""
    # TODO: in general, we should probably find a way to log all command invocations to the log file?
    if template_name and template_url:
        raise click.ClickException("Cannot specify both --template and --template-url")
    # parse this early to prevent frustration
    answers_dict = dict(answers)

    project_path = _get_project_path(directory_name)

    if template_name:
        template_url = _blessed_templates[template_name]
    elif template_url:
        logger.warning(_unofficial_template_warning)
        # note: we use unsafe_ask here (and everywhere else) so we don't have to
        # handle None returns for KeyboardInterrupt - click will handle these nicely enough for us
        # at the root level
        if not questionary.confirm("Continue anyway?", default=False).unsafe_ask():
            _fail_and_bail()
    else:
        template_url = _get_template_url()

    logger.debug(f"Attempting to initialise project in {project_path} from template {template_url}")

    copier_worker = copier.run_copy(template_url, project_path, data=answers_dict)
    expanded_template_url = copier_worker.template.url_expanded
    logger.debug(f"Project initialisation complete, final clone URL = {expanded_template_url}")
    if _should_attempt_git_init(use_git_option=use_git, project_path=project_path):
        _git_init(
            project_path, commit_message=f"Project initialised with AlgoKit CLI using template: {expanded_template_url}"
        )

    logger.info("🙌 Project initialized! For next steps, consult the documentation of your selected template 🧐")
    if re.search("https?://", expanded_template_url):
        # if the URL looks like an HTTP URL (should be the case for blessed templates), be helpful
        # and print it out so the user can (depending on terminal) click it to open in browser
        logger.info(f"Your selected template comes from:\n➡️  {expanded_template_url.removesuffix('.git')}")


def _fail_and_bail() -> Never:
    logger.info("🛑 Bailing out... 👋")
    raise click.exceptions.Exit(code=1)


class NonEmptyValidator(questionary.Validator):
    def validate(self, document: prompt_toolkit.document.Document) -> None:
        value = document.text.strip()
        if not value:
            raise questionary.ValidationError(message="Please enter a value")


class DirectoryNameValidator(questionary.Validator):
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def validate(self, document: prompt_toolkit.document.Document) -> None:
        name = document.text.strip()
        new_path = self._base_path / name
        if new_path.exists() and not new_path.is_dir():
            raise questionary.ValidationError(
                message="File with same name already exists in current directory, please enter a different name"
            )


class ChainedValidator(questionary.Validator):
    def __init__(self, *validators: questionary.Validator):
        self._validators = validators

    def validate(self, document: prompt_toolkit.document.Document) -> None:
        for validator in self._validators:
            validator.validate(document)


class GitRepoValidator(questionary.Validator):
    def validate(self, document: prompt_toolkit.document.Document) -> None:
        value = document.text.strip()
        if not value:
            return
        try:
            if copier.vcs.get_repo(value) is not None:
                return
        except Exception:
            logger.exception(f"Error parsing repo URL = {value}", extra=EXTRA_EXCLUDE_FROM_CONSOLE)
        raise questionary.ValidationError(message=f"Couldn't parse repo URL {value}. Try prefixing it with git+ ?")


def _get_project_path(directory_name_option: str | None = None) -> Path:
    base_path = Path.cwd()
    if directory_name_option is not None:
        directory_name = directory_name_option
    else:
        directory_name = questionary.text(
            "Name of directory to create the project in: ",
            validate=ChainedValidator(NonEmptyValidator(), DirectoryNameValidator(base_path)),
            validate_while_typing=False,
        ).unsafe_ask()
    project_path = base_path / directory_name.strip()
    if project_path.exists():
        logger.warning(
            "Re-using existing directory, this is not recommended because if project generation fails, "
            "then we can't automatically cleanup."
        )
        if not questionary.confirm("Continue anyway?", default=False).unsafe_ask():
            # re-prompt only if interactive and user didn't cancel
            if directory_name_option is None:
                return _get_project_path()
            else:
                _fail_and_bail()
    return project_path


def _get_template_url() -> str:
    choice_value = questionary.select(
        "Select a project template: ", choices=[*_blessed_templates, "<enter custom url>"]
    ).unsafe_ask()
    try:
        return _blessed_templates[choice_value]
    except KeyError:
        # user selected custom url
        pass
    # note we print the warning but don't prompt for confirmation like we would when the URL is passed
    # as a command line argument, instead we allow the user to return to the official selection list
    # by entering a blank string
    logger.warning(f"\n{_unofficial_template_warning}\n")
    logger.info(
        "Enter a custom project URL, or leave blank and press enter to go back to official template selection.\n"
        "Note that you can use gh: as a shorthand for github.com and likewise gl: for gitlab.com\n"
        "Valid examples:\n"
        " - gh:copier-org/copier\n"
        " - gl:copier-org/copier\n"
        " - git@github.com:copier-org/copier.git\n"
        " - git+https://mywebsiteisagitrepo.example.com/\n"
        " - /local/path/to/git/repo\n"
        " - /local/path/to/git/bundle/file.bundle\n"
        " - ~/path/to/git/repo\n"
        " - ~/path/to/git/repo.bundle\n"
    )
    template_url: str = (
        questionary.text("Custom template URL: ", validate=GitRepoValidator, validate_while_typing=False)
        .unsafe_ask()
        .strip()
    )
    # re-prompt if empty response
    return template_url or _get_template_url()


def _should_attempt_git_init(use_git_option: bool | None, project_path: Path) -> bool:
    if use_git_option is False:
        return False
    try:
        git_rev_parse_result = proc.run(["git", "rev-parse", "--show-toplevel"], cwd=project_path)
    except FileNotFoundError:
        logger.warning("git command wasn't found on your PATH, can not perform repository initialisation")
        return False
    is_in_git_repo = git_rev_parse_result.exit_code == 0
    if is_in_git_repo:
        logger.log(
            msg="Directory is already under git revision control, skipping git setup",
            # warning if the user explicitly requested to set up git, info otherwise
            level=logging.WARNING if use_git_option else logging.INFO,
        )
        return False

    return (
        use_git_option
        or questionary.confirm(
            "Would you like to initialise a git repository and perform an initial commit?"
        ).unsafe_ask()
    )


def _git_init(project_path: Path, commit_message: str) -> None:
    def git(*args: str, bad_exit_warn_message: str) -> bool:
        result = proc.run(["git", *args], cwd=project_path)
        success = result.exit_code == 0
        if not success:
            logger.warning(bad_exit_warn_message)
        return success

    if git("init", bad_exit_warn_message="Failed to initialise git repository"):
        if git("add", "--all", bad_exit_warn_message="Failed to add generated project files"):
            if git("commit", "-m", commit_message, bad_exit_warn_message="Initial commit failed"):
                logger.info("🎉 Performed initial git commit successfully! 🎉")
