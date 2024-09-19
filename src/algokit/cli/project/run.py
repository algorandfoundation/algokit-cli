import logging
from functools import cache
from pathlib import Path

import click

from algokit.cli.common.utils import MutuallyExclusiveOption, sanitize_extra_args
from algokit.core.project import ProjectType
from algokit.core.project.run import (
    ProjectCommand,
    WorkspaceProjectCommand,
    load_commands,
    run_command,
    run_workspace_command,
)

logger = logging.getLogger(__name__)


@cache
def _load_project_commands(project_dir: Path) -> dict[str, click.Command]:
    """
    Loads project commands from the .algokit.toml file located in the specified project directory.

    This function reads the project directory's .algokit.toml configuration file, extracts custom commands defined
    within it, and returns a dictionary mapping command names to their corresponding Click command objects.

    Args:
        project_dir (Path): The path to the project directory.

    Returns:
        dict[str, click.Command]: A dictionary where keys are command names and values are Click command objects.
    """

    custom_commands = load_commands(project_dir)

    if custom_commands is None:
        return {}

    commands_table: dict[str, click.Command] = {}

    for custom_command in custom_commands:
        # Define the base command function
        def base_command(  # noqa: PLR0913
            *,
            custom_command: ProjectCommand | WorkspaceProjectCommand = custom_command,
            project_names: tuple[str] | None = None,
            list_projects: bool = False,
            project_type: str | None = None,
            sequential: bool = False,
            extra_args: tuple[str, ...] | None = None,
        ) -> None:
            """
            Executes a base command function with optional parameters for listing projects or specifying project names.

            This function serves as the base for executing both ProjectCommand and WorkspaceProjectCommand instances.
            It handles listing projects within a workspace and executing commands for specific projects or all projects
            within a workspace.

            Args:
                extra_args (tuple[str, ...]): The command arguments to be passed to the custom command.
                custom_command (ProjectCommand | WorkspaceProjectCommand): The custom command to be executed.
                project_names (list[str] | None): Optional. A list of project names to execute the command on.
                list_projects (bool): Optional. A flag indicating whether to list projects associated
                with a workspace command.
                project_type (str | None): Optional. Only execute commands in projects of specified type.
                sequential (bool): Whether to execute wokspace commands sequentially. Defaults to False.
            Returns:
                None
            """
            extra_args = sanitize_extra_args(extra_args or ())
            if list_projects and isinstance(custom_command, WorkspaceProjectCommand):
                for command in custom_command.commands:
                    cmds = " && ".join(" ".join(cmd) for cmd in command.commands)
                    logger.info(f"ℹ️  Project: {command.project_name}, Command name: {command.name}, Command(s): {cmds}")  # noqa: RUF001
                return

            run_command(command=custom_command, extra_args=extra_args) if isinstance(
                custom_command, ProjectCommand
            ) else run_workspace_command(
                workspace_command=custom_command,
                project_names=list(project_names or []),
                project_type=project_type,
                sequential=sequential,
                extra_args=extra_args,
            )

        # Check if the command is a WorkspaceProjectCommand and conditionally decorate
        is_workspace_command = isinstance(custom_command, WorkspaceProjectCommand)
        command = click.argument("extra_args", nargs=-1, type=click.UNPROCESSED, required=False)(base_command)
        if is_workspace_command:
            command = click.option(
                "project_names",
                "--project-name",
                "-p",
                multiple=True,
                help=(
                    "Optional. Execute the command on specified projects. "
                    "Defaults to all projects in the current directory."
                ),
                nargs=1,
                default=[],
                required=False,
            )(base_command)
            command = click.option(
                "list_projects",
                "--list",
                "-l",
                help="(Optional) List all projects associated with workspace command",
                default=False,
                is_flag=True,
                type=click.BOOL,
                required=False,
                cls=MutuallyExclusiveOption,
                not_required_if=["project_names"],
            )(command)
            command = click.option(
                "project_type",
                "--type",
                "-t",
                type=click.Choice([ProjectType.FRONTEND, ProjectType.CONTRACT, ProjectType.BACKEND]),
                required=False,
                default=None,
                help="Limit execution to specific project types if executing from workspace. (Optional)",
            )(command)
            command = click.option(
                "sequential",
                "--sequential/--concurrent",
                "-s/-c",
                help="Execute workspace commands sequentially. Defaults to concurrent.",
                default=False,
                is_flag=True,
                required=False,
            )(command)

        # Apply the click.command decorator with common options
        command = click.command(
            name=custom_command.name,
            help=f"{custom_command.description}" or "Command description is not supplied.",
            context_settings={
                # Enables workspace commands in standalone projects without execution impact,
                # supporting uniform GitHub workflows across official templates.
                "ignore_unknown_options": not is_workspace_command,
            },
        )(command)

        commands_table[custom_command.name] = command

    return commands_table


class RunCommandGroup(click.Group):
    """
    A custom Click command group for dynamically loading and executing project commands.

    This command group overrides the default Click command loading mechanism to include dynamically loaded project
    commands from the .algokit.toml configuration file. It supports both predefined and dynamically loaded commands.
    """

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """
        Retrieves a command by name, including dynamically loaded project commands.

        Args:
            ctx (click.Context): The current Click context.
            cmd_name (str): The name of the command to retrieve.

        Returns:
            click.Command | None: The requested command if found; otherwise, None.
        """
        return_value = super().get_command(ctx, cmd_name)

        if return_value is not None:
            return return_value

        return _load_project_commands(Path.cwd()).get(cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        """
        Lists all available commands, including dynamically loaded project commands.

        Args:
            ctx (click.Context): The current Click context.

        Returns:
            list[str]: A sorted list of all available command names.
        """
        predefined_command_names = super().list_commands(ctx)
        dynamic_commands = _load_project_commands(Path.cwd())
        dynamic_command_names = list(dynamic_commands)

        return sorted(predefined_command_names + dynamic_command_names)


@click.group("run", cls=RunCommandGroup)
def run_group() -> None:
    """Define custom commands and manage their execution in you projects."""
