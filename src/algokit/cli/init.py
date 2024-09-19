import logging
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import NoReturn

import click
import prompt_toolkit.document
import questionary

from algokit.core import proc, questionary_extensions
from algokit.core.conf import get_algokit_config
from algokit.core.init import (
    append_project_to_vscode_workspace,
    get_git_user_info,
    is_valid_project_dir_name,
    resolve_vscode_workspace_file,
)
from algokit.core.log_handlers import EXTRA_EXCLUDE_FROM_CONSOLE
from algokit.core.project import ProjectType, get_workspace_project_path
from algokit.core.project.bootstrap import (
    MAX_BOOTSTRAP_DEPTH,
    bootstrap_any_including_subdirs,
    project_minimum_algokit_version_check,
)
from algokit.core.sandbox import DEFAULT_ALGOD_PORT, DEFAULT_ALGOD_SERVER, DEFAULT_ALGOD_TOKEN, DEFAULT_INDEXER_PORT
from algokit.core.utils import get_python_paths

logger = logging.getLogger(__name__)


DEFAULT_STATIC_ANSWERS: dict[str, str] = {
    "algod_token": DEFAULT_ALGOD_TOKEN,
    "algod_server": DEFAULT_ALGOD_SERVER,
    "algod_port": str(DEFAULT_ALGOD_PORT),
    "indexer_token": DEFAULT_ALGOD_TOKEN,
    "indexer_server": DEFAULT_ALGOD_SERVER,
    "indexer_port": str(DEFAULT_INDEXER_PORT),
}
DEFAULT_DYNAMIC_ANSWERS: dict[str, Callable[[], str]] = {
    "author_name": lambda: get_git_user_info("name") or "John Doe",
    "author_email": lambda: get_git_user_info("email") or "my@mail.com",
}


def _get_default_answers() -> dict[str, str]:
    """get all default answers"""
    return {**DEFAULT_STATIC_ANSWERS, **{k: v() for k, v in DEFAULT_DYNAMIC_ANSWERS.items()}}


"""Answers that are not really answers, but useful to pass through to templates in case they want to make use of them"""


class TemplatePresetType(str, Enum):
    """
    For distinguishing main template preset type question invoked by `algokit init`
    """

    SMART_CONTRACT = "Smart Contracts 📜"
    DAPP_FRONTEND = "DApp Frontend 🖥️"
    SMART_CONTRACT_AND_DAPP_FRONTEND = "Smart Contracts & DApp Frontend 🎛️"
    CUSTOM_TEMPLATE = "Custom Template 🛠️"


class ContractLanguage(Enum):
    """
    For programming languages that have corresponding smart contract languages
    """

    PYTHON = "Python 🐍"
    TYPESCRIPT = "TypeScript 📘"


class TemplateKey(str, Enum):
    """
    For templates included in wizard v2 by default
    """

    BASE = "base"
    PYTHON = "python"
    TEALSCRIPT = "tealscript"
    FULLSTACK = "fullstack"
    REACT = "react"
    BEAKER = "beaker"
    PLAYGROUND = "playground"


@dataclass(kw_only=True)
class TemplateSource:
    url: str
    commit: str | None = None
    """when adding a blessed template that is verified but not controlled by Algorand,
    ensure a specific commit is used"""
    branch: str | None = None
    answers: list[tuple[str, str]] | None = None

    def __str__(self) -> str:
        if self.commit:
            return "@".join([self.url, self.commit])
        return self.url


@dataclass(kw_only=True)
class BlessedTemplateSource(TemplateSource):
    description: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlessedTemplateSource):
            return NotImplemented
        return self.description == other.description and self.url == other.url


LANGUAGE_TO_TEMPLATE_MAP = {
    ContractLanguage.PYTHON: TemplateKey.PYTHON,
    ContractLanguage.TYPESCRIPT: TemplateKey.TEALSCRIPT,
}


# Please note, the main reason why below is a function is due to the need to patch the values in unit/approval tests
def _get_blessed_templates() -> dict[TemplateKey, BlessedTemplateSource]:
    return {
        TemplateKey.TEALSCRIPT: BlessedTemplateSource(
            url="gh:algorand-devrel/tealscript-algokit-template",
            description="Official starter template for TEALScript applications.",
        ),
        TemplateKey.PYTHON: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-python-template",
            description="Official starter template for Algorand Python applications",
        ),
        TemplateKey.REACT: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-react-frontend-template",
            description="Official template for React frontend applications (smart contracts not included).",
        ),
        TemplateKey.FULLSTACK: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-fullstack-template",
            description="Official template for starter or production fullstack applications.",
        ),
        TemplateKey.BASE: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-base-template",
            description="Official base template for enforcing workspace structure for standalone AlgoKit projects.",
        ),
        TemplateKey.PLAYGROUND: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-beaker-playground-template",
            description="Official template showcasing a number of small example applications and demos.",
        ),
    }


_unofficial_template_warning = (
    "Community templates have not been reviewed, and can execute arbitrary code.\n"
    "Please inspect the template repository, and pay particular attention to the "
    "values of _tasks, _migrations and _jinja_extensions in copier.yml"
)


def _validate_dir_name(context: click.Context, param: click.Parameter, value: str | None) -> str | None:
    if value is not None and not is_valid_project_dir_name(value):
        raise click.BadParameter(
            "Invalid directory name. Ensure it's a mix of letters, numbers, dashes, "
            "periods, and/or underscores, and not already used.",
            context,
            param,
        )
    return value


def _prevent_workspace_nesting(*, workspace_path: Path | None, project_path: Path, use_workspace: bool) -> None:
    if not workspace_path:
        return

    if use_workspace and workspace_path != project_path.parent:
        logger.error(
            "Error: Workspace nesting detected. Please run 'init' from the workspace root: "
            f"'{workspace_path}'. For more info, refer to "
            "https://github.com/algorandfoundation/algokit-cli/blob/main/docs/features/project/run.md"
        )
        _fail_and_bail()


@click.command("init", short_help="Initializes a new project from a template; run from project parent directory.")
@click.option(
    "directory_name",
    "--name",
    "-n",
    type=str,
    help="Name of the project / directory / repository to create.",
    callback=_validate_dir_name,
)
@click.option(
    "template_name",
    "--template",
    "-t",
    type=click.Choice([k.value for k in _get_blessed_templates()]),
    default=None,
    help="Name of an official template to use. To choose interactively, run this command with no arguments.",
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
    help="Whether to run `algokit project bootstrap` to install and configure the new project's dependencies locally.",
)
@click.option(
    "open_ide",
    "--ide/--no-ide",
    is_flag=True,
    default=True,
    help="Whether to open an IDE for you if the IDE and IDE config are detected. Supported IDEs: VS Code.",
)
@click.option(
    "use_workspace",
    "--workspace/--no-workspace",
    is_flag=True,
    default=True,
    help=(
        "Whether to prefer structuring standalone projects as part of a workspace. "
        "An AlgoKit workspace is a conventional project structure that allows managing "
        "multiple standalone projects in a monorepo."
    ),
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
def init_command(  # noqa: PLR0913, C901, PLR0915
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
    use_workspace: bool,
    open_ide: bool,
) -> None:
    """
    Initializes a new project from a template, including prompting
    for template specific questions to be used in template rendering.

    Templates can be default templates shipped with AlgoKit, or custom
    templates in public Git repositories.

    Includes ability to initialise Git repository, run algokit project bootstrap and
    automatically open Visual Studio Code.

    This should be run in the parent directory that you want the project folder
    created in.

    By default, the `--workspace` flag creates projects within a workspace structure or integrates them into an existing
    one, promoting organized management of multiple projects. Alternatively,
    to disable this behavior use the `--no-workspace` flag, which ensures
    the new project is created in a standalone target directory. This is
    suitable for isolated projects or when workspace integration is unnecessary.
    """

    if not shutil.which("git"):
        raise click.ClickException(
            "Git not found; please install git and add to path.\n"
            "See https://github.com/git-guides/install-git for more information."
        )

    # parse the input early to prevent frustration - combined with some defaults but they can be overridden
    answers_dict = _get_default_answers() | dict(answers)

    template = _get_template(
        name=template_name,
        url=template_url,
        commit=template_url_ref,
        unsafe_security_accept_template_url=unsafe_security_accept_template_url,
    )

    for custom_answer in template.answers or []:
        answers_dict.setdefault(*custom_answer)

    logger.debug(f"template source = {template}")

    # allow skipping prompt if the template is the base template to avoid redundant
    # 're-using existing directory' warning in fullstack template init
    project_path, overwrite_existing_dir = _get_project_path(
        directory_name_option=directory_name, force=template == _get_blessed_templates()[TemplateKey.BASE]
    )
    workspace_path = get_workspace_project_path(project_path)
    if not overwrite_existing_dir:
        _prevent_workspace_nesting(
            workspace_path=workspace_path, project_path=project_path, use_workspace=use_workspace
        )

    logger.debug(f"project path = {project_path}")
    directory_name = project_path.name
    # provide the directory name as an answer to the template, if not explicitly overridden by user
    answers_dict.setdefault("project_name", directory_name)

    system_python_path = next(get_python_paths(), None)
    if system_python_path is not None:
        answers_dict.setdefault("python_path", system_python_path)
    else:
        answers_dict.setdefault("python_path", "no_system_python_available")

    project_path = _resolve_workspace_project_path(
        template_source=template, project_path=project_path, use_workspace=use_workspace
    )
    answers_dict.setdefault("use_workspace", "yes" if use_workspace else "no")

    logger.info(f"Starting template copy and render at {project_path}...")
    # copier is lazy imported for two reasons
    # 1. it is slow to import on first execution after installing
    # 2. the import fails if git is not installed (which we check above)
    # TODO: copier is typed, need to figure out how to force mypy to accept that or submit a PR
    #       to their repo to include py.typed file
    from copier.main import Worker

    from algokit.core.init import populate_default_answers

    expected_answers_file = project_path / ".algokit" / ".copier-answers.yml"
    relative_answers_file = expected_answers_file.relative_to(project_path) if expected_answers_file.exists() else None

    with Worker(
        src_path=template.url,
        dst_path=project_path,
        answers_file=relative_answers_file,
        data=answers_dict,
        quiet=True,
        vcs_ref=template.branch or template.commit,
        unsafe=True,
    ) as copier_worker:
        if use_defaults:
            populate_default_answers(copier_worker)
        expanded_template_url = copier_worker.template.url_expanded
        logger.debug(f"final clone URL = {expanded_template_url}")
        copier_worker.run_copy()

    logger.info("Template render complete!")

    # reload workspace path cause it might have been just introduced with new project instance
    workspace_path = get_workspace_project_path(project_path)

    _maybe_move_github_folder(project_path=project_path, use_workspace=use_workspace)

    _maybe_bootstrap(project_path, run_bootstrap=run_bootstrap, use_defaults=use_defaults, use_workspace=use_workspace)

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
    vscode_workspace_file = resolve_vscode_workspace_file(workspace_path or project_path)

    if vscode_workspace_file:
        append_project_to_vscode_workspace(project_path=project_path, workspace_path=vscode_workspace_file)

    # Below must be ensured to run after all required filesystem changes are applied to ensure first commit captures
    # all the changes introduced by init invocation
    _maybe_git_init(
        workspace_path or project_path,
        use_git=use_git,
        commit_message=f"Project initialised with AlgoKit CLI using template: {expanded_template_url}",
    )

    if (
        open_ide
        and ((project_path / ".vscode").is_dir() or vscode_workspace_file)
        and (code_cmd := shutil.which("code"))
    ):
        target_path = str(vscode_workspace_file if vscode_workspace_file else project_path)

        logger.info(
            "VSCode configuration detected in project directory, and 'code' command is available on path, "
            "attempting to launch VSCode"
        )

        code_cmd_and_args = [code_cmd, target_path]

        if readme_path:
            code_cmd_and_args.append(str(readme_path))

        proc.run(code_cmd_and_args)
    elif readme_path:
        logger.info(f"Your template includes a {readme_path.name} file, you might want to review that as a next step.")


def _maybe_bootstrap(
    project_path: Path, *, run_bootstrap: bool | None, use_defaults: bool, use_workspace: bool
) -> None:
    if run_bootstrap is None:
        # if user didn't specify a bootstrap option, then assume yes if using defaults, otherwise prompt
        run_bootstrap = use_defaults or questionary_extensions.prompt_confirm(
            "Do you want to run `algokit project bootstrap` for this new project? "
            "This will install and configure dependencies allowing it to be run immediately.",
            default=True,
        )
    if run_bootstrap:
        # note: we run bootstrap before git commit so that we can commit any lock files,
        # but if something goes wrong, we don't want to block
        try:
            project_minimum_algokit_version_check(project_path)

            # if user prefers to ignore creating the `workspace` setup, set bootstrap depth to 1 else default
            bootstrap_depth = 1 if not use_workspace else MAX_BOOTSTRAP_DEPTH
            bootstrap_any_including_subdirs(project_path, ci_mode=False, max_depth=bootstrap_depth)
        except Exception as e:
            logger.error(f"Received an error while attempting bootstrap: {e}")
            logger.exception(
                "Bootstrap failed. Once any errors above are resolved, "
                f"you can run `algokit project bootstrap` in {project_path}",
                exc_info=e,
            )


def _maybe_git_init(project_path: Path, *, use_git: bool | None, commit_message: str) -> None:
    if _should_attempt_git_init(use_git_option=use_git, project_path=project_path):
        _git_init(project_path, commit_message=commit_message)


def _maybe_move_github_folder(*, project_path: Path, use_workspace: bool) -> None:
    """Move contents of .github folder from project_path to the root of the workspace if exists
    and the workspace is used.

    Args:
        project_path: The path to the project directory.
        use_workspace: A flag to indicate if the project is initialized with workspace flag
    """

    source_dir = project_path / ".github"

    if (
        not use_workspace
        or not source_dir.exists()
        or not (workspace_root := get_workspace_project_path(project_path.parent))
    ):
        return

    target_dir = workspace_root / ".github"

    for source_file in source_dir.rglob("*"):
        if source_file.is_file():
            target_file = target_dir / source_file.relative_to(source_dir)

            if target_file.exists():
                logger.debug(f"Skipping move of {source_file.name} to {target_file} (duplicate exists)")
                continue

            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_file), str(target_file))
            except shutil.Error as e:
                logger.debug(f"Skipping move of {source_file} to {target_file}: {e}")

    if any(p.is_file() for p in source_dir.rglob("*")):
        click.secho(
            "Failed to move all files within your project's .github folder to the workspace root. "
            "Please review any files that remain in your project's .github folder and manually include "
            "in the root .github directory as required.",
            fg="yellow",
        )
    else:
        shutil.rmtree(source_dir)
        logger.debug(f"No files found in .github folder after merge. Removing `.github` directory at {source_dir}...")


def _fail_and_bail() -> NoReturn:
    logger.info("🛑 Bailing out... 👋")
    raise click.exceptions.Exit(code=1)


def _repo_url_is_valid(url: str) -> bool:
    """Check the repo URL is valid according to copier"""
    from copier.vcs import get_repo

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
        if not is_valid_project_dir_name(document.text):
            raise questionary.ValidationError(
                message="Invalid name. Use letters, numbers, dashes, periods, underscores, and ensure it's unique.",
                cursor_position=len(document.text),
            )


def _get_project_path(*, directory_name_option: str | None = None, force: bool = False) -> tuple[Path, bool]:
    """
    Determines the project path based on the provided directory name option.

    Args:
        directory_name_option: The name of the directory provided by the user.
                               If None, the user will be prompted to enter a name.
        force: A flag to auto accept warning prompts.

    Returns:
        The path to the project directory and a flag to indicate if the user agreed to overwrite the directory.
    """

    base_path = Path.cwd()
    overwrite_existing_dir = force
    directory_name = (
        directory_name_option
        if directory_name_option is not None
        else questionary_extensions.prompt_text(
            "Name of project / directory to create the project in:",
            validators=[questionary_extensions.NonEmptyValidator(), DirectoryNameValidator(base_path)],
        )
    ).strip()

    project_path = base_path / directory_name
    if project_path.exists() and not project_path.is_dir():
        logger.error("A file with the same name already exists in the current directory. Please use a different name.")
        _fail_and_bail()

    if project_path.is_dir() and not force:
        logger.warning(
            "Re-using existing directory, this is not recommended because if project "
            "generation fails, then we can't automatically cleanup."
        )
        overwrite_existing_dir = questionary_extensions.prompt_confirm("Continue anyway?", default=False)
        if not overwrite_existing_dir:
            return _get_project_path() if directory_name_option is None else _fail_and_bail()

    return project_path, overwrite_existing_dir


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
        template: TemplateSource = blessed_templates[TemplateKey(name)]
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
    project_type = questionary_extensions.prompt_select(
        "Which of these options best describes the project you want to build?",
        *[questionary.Choice(title=p_type.value, value=p_type) for p_type in TemplatePresetType],  # Modified line
    )
    logger.debug(f"selected project_type = {project_type.value}")

    template = None
    language = None
    if project_type in [TemplatePresetType.SMART_CONTRACT, TemplatePresetType.SMART_CONTRACT_AND_DAPP_FRONTEND]:
        language = questionary_extensions.prompt_select(
            "Which language would you like to use for the smart contract?",
            *[questionary.Choice(title=lang.value, value=lang) for lang in ContractLanguage],
        )
        logger.debug(f"selected language = {language}")
        template = (
            TemplateKey.FULLSTACK
            if project_type == TemplatePresetType.SMART_CONTRACT_AND_DAPP_FRONTEND
            else LANGUAGE_TO_TEMPLATE_MAP[language]
        )

    elif project_type == TemplatePresetType.DAPP_FRONTEND:
        template = TemplateKey.REACT

    # Ensure a template has been selected
    if not template and not project_type == TemplatePresetType.CUSTOM_TEMPLATE:
        raise click.ClickException("No template selected. Please try again.")

    # Map the template string directly to the TemplateSource
    # This is needed to be able to reuse fullstack to work with beaker, python, and tealscript templates
    blessed_templates = _get_blessed_templates()
    if template in blessed_templates:
        selected_template_source = blessed_templates[template]
        if template == TemplateKey.FULLSTACK and language is not None:
            smart_contract_template = LANGUAGE_TO_TEMPLATE_MAP[language]
            selected_template_source.answers = [("contract_template", smart_contract_template)]
        return selected_template_source

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
    template_url = questionary_extensions.prompt_text("Custom template URL:", validators=[GitRepoValidator()]).strip()
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


def _resolve_workspace_project_path(
    *, template_source: TemplateSource, project_path: Path, use_workspace: bool = True
) -> Path:
    blessed_template = _get_blessed_templates()

    # If its already a Base template, do not modify project path
    if template_source == blessed_template[TemplateKey.BASE]:
        return project_path

    cwd = Path.cwd()
    is_standalone = template_source != blessed_template[TemplateKey.FULLSTACK]
    config = get_algokit_config(project_dir=cwd)

    # 1. If standalone project (not fullstack) and use_workspace is True, bootstrap algokit-base-template
    if config is None and is_standalone and use_workspace:
        _init_base_template(target_path=project_path, is_blessed=template_source in blessed_template.values())

        config = get_algokit_config(project_dir=project_path)
        if not config:
            logger.error("Failed to instantiate workspace structure for standalone project")
            _fail_and_bail()

        sub_projects_path = config.get("project", {}).get("projects_root_path") or "projects"
        new_project_path = cwd / project_path.name / sub_projects_path / project_path.name
        new_project_path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Workspace structure is ready! The project is to be placed under {new_project_path}")
        return new_project_path

    # 2. If its a standalone project being instantiated inside an existing workspace project and use_workspace is True
    # then place the new project inside expected projects folder defined by workspace toml
    if (
        config
        and config.get("project", {}).get("type") == ProjectType.WORKSPACE.value
        and is_standalone
        and use_workspace
    ):
        sub_projects_path = config.get("project", {}).get("projects_root_path") or "projects"
        projects_root = cwd / sub_projects_path
        logger.debug(f"Workspace structure detected! Moving the project to be instantiated into {projects_root}")
        return projects_root / project_path.name

    return project_path


def _init_base_template(*, target_path: Path, is_blessed: bool) -> None:
    """
    Instantiate the base template for a standalone project.
    Sets up the common workspace structure for standalone projects.

    Args:
        target_path: The path to the project directory.
        is_blessed: Whether the template is a blessed template.
    """

    # Instantiate the base template
    blessed_templates = _get_blessed_templates()
    base_template = blessed_templates[TemplateKey.BASE]
    base_template_answers = {
        "use_default_readme": "yes",
        "project_name": target_path.name,
        "projects_root_path": "projects",
        "include_github_workflow_template": not is_blessed,
    }
    from copier.main import Worker

    with Worker(
        src_path=base_template.url,
        dst_path=target_path,
        data=base_template_answers,
        quiet=True,
        vcs_ref=base_template.branch or base_template.commit,
        unsafe=True,
    ) as copier_worker:
        copier_worker.run_copy()
