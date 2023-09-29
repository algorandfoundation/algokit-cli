import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import click
import prompt_toolkit.document
import questionary

from algokit.core import proc, questionary_extensions
from algokit.core.bootstrap import bootstrap_any_including_subdirs, project_minimum_algokit_version_check
from algokit.core.log_handlers import EXTRA_EXCLUDE_FROM_CONSOLE
from algokit.core.sandbox import DEFAULT_ALGOD_PORT, DEFAULT_ALGOD_SERVER, DEFAULT_ALGOD_TOKEN, DEFAULT_INDEXER_PORT

logger = logging.getLogger(__name__)


DEFAULT_ANSWERS: dict[str, str] = {
    "algod_token": DEFAULT_ALGOD_TOKEN,
    "algod_server": DEFAULT_ALGOD_SERVER,
    "algod_port": str(DEFAULT_ALGOD_PORT),
    "indexer_token": DEFAULT_ALGOD_TOKEN,
    "indexer_server": DEFAULT_ALGOD_SERVER,
    "indexer_port": str(DEFAULT_INDEXER_PORT),
}
"""Answers that are not really answers, but useful to pass through to templates in case they want to make use of them"""


@dataclass(kw_only=True)
class TemplateSource:
    url: str
    commit: str | None = None
    """when adding a blessed template that is verified but not controlled by Algorand,
    ensure a specific commit is used"""

    def __str__(self) -> str:
        if self.commit:
            return "@".join([self.url, self.commit])
        return self.url


@dataclass(kw_only=True)
class BlessedTemplateSource(TemplateSource):
    description: str


# this is a function so we can modify the values in unit tests
def _get_blessed_templates() -> dict[str, BlessedTemplateSource]:
    return {
        "beaker": BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-beaker-default-template",
            description="Official template for starter or production Beaker applications.",
        ),
        "tealscript": BlessedTemplateSource(
            url="gh:algorand-devrel/tealscript-algokit-template",
            description="Official starter template for TEALScript applications.",
        ),
        "react": BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-react-frontend-template",
            description="Official template for React frontend applications (smart contracts not included).",
        ),
        "fullstack": BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-fullstack-template",
            description="Official template for starter or production fullstack applications (React + Beaker).",
        ),
        "playground": BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-beaker-playground-template",
            description="Official template showcasing a number of small example applications and demos.",
        ),
    }


_unofficial_template_warning = (
    "Community templates have not been reviewed, and can execute arbitrary code.\n"
    "Please inspect the template repository, and pay particular attention to the "
    "values of _tasks, _migrations and _jinja_extensions in copier.yml"
)


def validate_dir_name(context: click.Context, param: click.Parameter, value: str | None) -> str | None:
    if value is not None and not re.match(r"^[\w\-.]+$", value):
        raise click.BadParameter(
            "Received invalid value for directory name; "
            "expected a mix of letters (a-z, A-Z), numbers (0-9), dashes (-), periods (.) and/or underscores (_)",
            context,
            param,
        )
    return value


@click.command("init", short_help="Initializes a new project from a template; run from project parent directory.")
@click.option(
    "directory_name",
    "--name",
    "-n",
    type=str,
    help="Name of the project / directory / repository to create.",
    callback=validate_dir_name,
)
@click.option(
    "template_name",
    "--template",
    "-t",
    type=click.Choice(list(_get_blessed_templates())),
    default=None,
    help="Name of an official template to use. To see a list of descriptions, run this command with no arguments.",
)
@click.option(
    "--template-url",
    type=str,
    default=None,
    help="URL to a git repo with a custom project template.",
    metavar="URL",
)
@click.option(
    "--template-url-ref",
    type=str,
    default=None,
    help="Specific tag, branch or commit to use on git repo specified with --template-url. Defaults to latest.",
    metavar="URL",
)
@click.option(
    "--UNSAFE-SECURITY-accept-template-url",
    is_flag=True,
    default=False,
    help=(
        "Accept the specified template URL, "
        "acknowledging the security implications of arbitrary code execution trusting an unofficial template."
    ),
)
@click.option("use_git", "--git/--no-git", default=None, help="Initialise git repository in directory after creation.")
@click.option(
    "use_defaults",
    "--defaults",
    is_flag=True,
    default=False,
    help="Automatically choose default answers without asking when creating this template.",
)
@click.option(
    "run_bootstrap",
    "--bootstrap/--no-bootstrap",
    is_flag=True,
    default=None,
    help="Whether to run `algokit bootstrap` to install and configure the new project's dependencies locally.",
)
@click.option(
    "open_ide",
    "--ide/--no-ide",
    is_flag=True,
    default=True,
    help="Whether to open an IDE for you if the IDE and IDE config are detected. Supported IDEs: VS Code.",
)
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
def init_command(  # noqa: PLR0913
    *,
    directory_name: str | None,
    template_name: str | None,
    template_url: str | None,
    template_url_ref: str | None,
    unsafe_security_accept_template_url: bool,
    use_git: bool | None,
    answers: list[tuple[str, str]],
    use_defaults: bool,
    run_bootstrap: bool | None,
    open_ide: bool,
) -> None:
    """
    Initializes a new project from a template, including prompting
    for template specific questions to be used in template rendering.

    Templates can be default templates shipped with AlgoKit, or custom
    templates in public Git repositories.

    Includes ability to initialise Git repository, run algokit bootstrap and
    automatically open Visual Studio Code.

    This should be run in the parent directory that you want the project folder
    created in.
    """

    if not shutil.which("git"):
        raise click.ClickException(
            "Git not found; please install git and add to path.\n"
            "See https://github.com/git-guides/install-git for more information."
        )

    # parse the input early to prevent frustration - combined with some defaults but they can be overridden
    answers_dict = DEFAULT_ANSWERS | dict(answers)

    template = _get_template(
        name=template_name,
        url=template_url,
        commit=template_url_ref,
        unsafe_security_accept_template_url=unsafe_security_accept_template_url,
    )
    logger.debug(f"template source = {template}")

    project_path = _get_project_path(directory_name)
    logger.debug(f"project path = {project_path}")
    directory_name = project_path.name
    # provide the directory name as an answer to the template, if not explicitly overridden by user
    answers_dict.setdefault("project_name", directory_name)

    logger.info("Starting template copy and render...")
    # copier is lazy imported for two reasons
    # 1. it is slow to import on first execution after installing
    # 2. the import fails if git is not installed (which we check above)
    # TODO: copier is typed, need to figure out how to force mypy to accept that or submit a PR
    #       to their repo to include py.typed file
    from copier.main import Worker  # type: ignore[import]

    from algokit.core.init import populate_default_answers

    with Worker(
        src_path=template.url,
        dst_path=project_path,
        data=answers_dict,
        quiet=True,
        vcs_ref=template.commit,
    ) as copier_worker:
        if use_defaults:
            populate_default_answers(copier_worker)
        expanded_template_url = copier_worker.template.url_expanded
        logger.debug(f"final clone URL = {expanded_template_url}")
        copier_worker.run_copy()

    logger.info("Template render complete!")

    _maybe_bootstrap(project_path, run_bootstrap=run_bootstrap, use_defaults=use_defaults)

    _maybe_git_init(
        project_path,
        use_git=use_git,
        commit_message=f"Project initialised with AlgoKit CLI using template: {expanded_template_url}",
    )

    logger.info(
        f"🙌 Project initialized at `{directory_name}`! For template specific next steps, "
        "consult the documentation of your selected template 🧐"
    )
    if re.search("https?://", expanded_template_url):
        # if the URL looks like an HTTP URL (should be the case for blessed templates), be helpful
        # and print it out so the user can (depending on terminal) click it to open in browser
        logger.info(f"Your selected template comes from:\n➡️  {expanded_template_url.removesuffix('.git')}")

    # Check if a README file exists
    readme_path = next(project_path.glob("README*"), None)

    # Check if a .workspace file exists
    workspace_file = next(project_path.glob("*.code-workspace"), None)

    if open_ide and (project_path / ".vscode").is_dir() and (code_cmd := shutil.which("code")):
        target_path = str(project_path)

        logger.info(
            "VSCode configuration detected in project directory, and 'code' command is available on path, "
            "attempting to launch VSCode"
        )

        if workspace_file:
            logger.info(f"Detected VSCode workspace file. Opening workspace: {workspace_file}")
            target_path = str(workspace_file)

        code_cmd_and_args = [code_cmd, target_path]

        if readme_path:
            code_cmd_and_args.append(str(readme_path))

        proc.run(code_cmd_and_args)
    elif readme_path:
        logger.info(f"Your template includes a {readme_path.name} file, you might want to review that as a next step.")


def _maybe_bootstrap(project_path: Path, *, run_bootstrap: bool | None, use_defaults: bool) -> None:
    if run_bootstrap is None:
        # if user didn't specify a bootstrap option, then assume yes if using defaults, otherwise prompt
        run_bootstrap = use_defaults or questionary_extensions.prompt_confirm(
            "Do you want to run `algokit bootstrap` for this new project? "
            "This will install and configure dependencies allowing it to be run immediately.",
            default=True,
        )
    if run_bootstrap:
        # note: we run bootstrap before git commit so that we can commit any lock files,
        # but if something goes wrong, we don't want to block
        try:
            project_minimum_algokit_version_check(project_path)
            bootstrap_any_including_subdirs(project_path, ci_mode=False)
        except Exception as e:
            logger.error(f"Received an error while attempting bootstrap: {e}")
            logger.exception(
                "Bootstrap failed. Once any errors above are resolved, "
                f"you can run `algokit bootstrap` in {project_path}",
                exc_info=e,
            )


def _maybe_git_init(project_path: Path, *, use_git: bool | None, commit_message: str) -> None:
    if _should_attempt_git_init(use_git_option=use_git, project_path=project_path):
        _git_init(project_path, commit_message=commit_message)


def _fail_and_bail() -> NoReturn:
    logger.info("🛑 Bailing out... 👋")
    raise click.exceptions.Exit(code=1)


def _repo_url_is_valid(url: str) -> bool:
    """Check the repo URL is valid according to copier"""
    from copier.vcs import get_repo  # type: ignore[import]

    if not url:
        return False
    try:
        return get_repo(url) is not None
    except Exception:
        logger.exception(f"Error parsing repo URL = {url}", extra=EXTRA_EXCLUDE_FROM_CONSOLE)
        return False


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


def _get_project_path(directory_name_option: str | None = None) -> Path:
    base_path = Path.cwd()
    if directory_name_option is not None:
        directory_name = directory_name_option
    else:
        directory_name = questionary_extensions.prompt_text(
            "Name of project / directory to create the project in: ",
            validators=[questionary_extensions.NonEmptyValidator(), DirectoryNameValidator(base_path)],
        )
    project_path = base_path / directory_name.strip()
    if project_path.exists():
        # NOTE: could get non-dir if passed as command line argument (we validate this interactively)
        if not project_path.is_dir():
            logger.error("File with same name already exists in current directory, please supply a different name")
            _fail_and_bail()
        logger.warning(
            "Re-using existing directory, this is not recommended because if project generation fails, "
            "then we can't automatically cleanup."
        )
        if not questionary_extensions.prompt_confirm("Continue anyway?", default=False):
            # re-prompt only if interactive and user didn't cancel
            if directory_name_option is None:
                return _get_project_path()
            else:
                _fail_and_bail()
    return project_path


def _get_template(
    *,
    name: str | None,
    url: str | None,
    commit: str | None,
    unsafe_security_accept_template_url: bool,
) -> TemplateSource:
    if name:
        if url:
            raise click.ClickException("Cannot specify both --template and --template-url")
        if commit:
            raise click.ClickException("--template-url-ref has no effect when template name is specified")
        blessed_templates = _get_blessed_templates()
        template: TemplateSource = blessed_templates[name]
    elif not url:
        template = _get_template_interactive()
    else:
        if not _repo_url_is_valid(url):
            logger.error(f"Couldn't parse repo URL {url}. Try prefixing it with git+ ?")
            _fail_and_bail()
        logger.warning(_unofficial_template_warning)
        # note: we use unsafe_ask here (and everywhere else) so we don't have to
        # handle None returns for KeyboardInterrupt - click will handle these nicely enough for us
        # at the root level
        if not (
            unsafe_security_accept_template_url
            or questionary_extensions.prompt_confirm("Continue anyway?", default=False)
        ):
            _fail_and_bail()
        template = TemplateSource(url=url, commit=commit)
    return template


class GitRepoValidator(questionary.Validator):
    def validate(self, document: prompt_toolkit.document.Document) -> None:
        value = document.text.strip()
        if value and not _repo_url_is_valid(value):
            raise questionary.ValidationError(message=f"Couldn't parse repo URL {value}. Try prefixing it with git+ ?")


def _get_template_interactive() -> TemplateSource:
    description_prefix = "\n     "

    choice_value = questionary_extensions.prompt_select(
        "Select a project template: ",
        *[
            questionary.Choice(
                title=[("bold", key), ("", description_prefix + tmpl.description)],
                value=tmpl,
            )
            for key, tmpl in _get_blessed_templates().items()
        ],
        f"<other>{description_prefix}Enter a custom URL - potentially dangerous!",
    )
    if isinstance(choice_value, TemplateSource):
        return choice_value
    # else: user selected custom url
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
    template_url = questionary_extensions.prompt_text("Custom template URL: ", validators=[GitRepoValidator()]).strip()
    if not template_url:
        # re-prompt if empty response
        return _get_template_interactive()
    return TemplateSource(url=template_url)


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

    return use_git_option or questionary_extensions.prompt_confirm(
        "Would you like to initialise a git repository and perform an initial commit?",
        default=True,
    )


def _git_init(project_path: Path, commit_message: str) -> None:
    def git(*args: str, bad_exit_warn_message: str) -> bool:
        result = proc.run(["git", *args], cwd=project_path)
        success = result.exit_code == 0
        if not success:
            logger.warning(bad_exit_warn_message)
        return success

    if (
        git("init", bad_exit_warn_message="Failed to initialise git repository")
        and git("checkout", "-b", "main", bad_exit_warn_message="Failed to name initial branch")
        and git("add", "--all", bad_exit_warn_message="Failed to add generated project files")
        and git("commit", "-m", commit_message, bad_exit_warn_message="Initial commit failed")
    ):
        logger.info("🎉 Performed initial git commit successfully! 🎉")
