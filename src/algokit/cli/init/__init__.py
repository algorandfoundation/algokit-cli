import click

# Import the core logic function from command.py
from algokit.cli.init.command import initialize_new_project

# Import the example subcommand
from algokit.cli.init.example import example_command

# Import necessary helpers/validators directly needed for options
from algokit.cli.init.helpers import (  # Assuming helpers are moved to a separate file or kept here
    _get_blessed_templates,
    _validate_dir_name,
)


# Define the group, allow invocation without subcommand, define ALL original options here
@click.group(
    "init",
    invoke_without_command=True,
    short_help="Initializes a new project from a template; run from project parent directory.",
)
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
@click.pass_context
def init_group(  # noqa: PLR0913
    ctx: click.Context,
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

    if ctx.invoked_subcommand is None:
        # No subcommand was called, so execute the default init logic
        # Pass all the options received by the group down to the implementation function
        initialize_new_project(
            directory_name=directory_name,
            template_name=template_name,
            template_url=template_url,
            template_url_ref=template_url_ref,
            unsafe_security_accept_template_url=unsafe_security_accept_template_url,
            use_git=use_git,
            answers=answers,
            use_defaults=use_defaults,
            run_bootstrap=run_bootstrap,
            use_workspace=use_workspace,
            open_ide=open_ide,
        )
    # else: a subcommand was invoked


# Add the subcommands to the group
init_group.add_command(example_command)
