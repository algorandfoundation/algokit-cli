import logging
from functools import cache
from pathlib import Path

import click

from algokit.cli.common.utils import MutuallyExclusiveOption
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
    Load project commands from .algokit.toml file.
    :param project_dir: Project directory path.
    :return: Custom generate commands.
    """

    custom_commands = load_commands(project_dir)

    if custom_commands is None:
        return {}

    commands_table: dict[str, click.Command] = {}

    for custom_command in custom_commands:
        # Define the base command function
        def base_command(
            *,
            custom_command: ProjectCommand | WorkspaceProjectCommand = custom_command,
            project_names: list[str] | None = None,
            list_projects: bool = False,
        ) -> None:
            if list_projects and isinstance(custom_command, WorkspaceProjectCommand):
                for command in custom_command.commands:
                    logger.info(
                        f"ℹ️ Project: {command.project_name}, "  # noqa: RUF001
                        f"Command name: {command.name}, "
                        f"Command: {' '.join(command.command)}"
                    )
                return None

            if isinstance(custom_command, ProjectCommand) and list_projects:
                raise click.ClickException("--list is only available for workspace commands.")

            return (
                run_command(command=custom_command)
                if isinstance(custom_command, ProjectCommand)
                else run_workspace_command(custom_command, project_names)
            )

        # Check if the command is a WorkspaceProjectCommand and conditionally decorate
        if isinstance(custom_command, WorkspaceProjectCommand):
            command = click.option(
                "project_names",
                "--project_name",
                "-p",
                multiple=True,
                help="Projects to execute the command on. (Defaults to all projects in the workspace)",
                nargs=1,
                required=False,
                cls=MutuallyExclusiveOption,
                not_required_if=["list"],
            )(base_command)
            command = click.option(
                "list_projects",
                "--list",
                "-l",
                help="List all projects associated with workspace command",
                default=False,
                is_flag=True,
                type=click.BOOL,
                required=False,
                cls=MutuallyExclusiveOption,
                not_required_if=["project_name"],
            )(command)
        else:
            command = base_command

        # Apply the click.command decorator with common options
        command = click.command(
            name=custom_command.name, help=f"{custom_command.description}" or "Command description is not supplied."
        )(command)

        commands_table[custom_command.name] = command

    return commands_table


class RunCommandGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return_value = super().get_command(ctx, cmd_name)

        if return_value is not None:
            return return_value

        return _load_project_commands(Path.cwd()).get(cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        predefined_command_names = super().list_commands(ctx)
        dynamic_commands = _load_project_commands(Path.cwd())
        dynamic_command_names = list(dynamic_commands)

        return sorted(predefined_command_names + dynamic_command_names)


@click.group("run", cls=RunCommandGroup)
def run_group() -> None:
    """Define custom commands and manage their execution in you projects."""
