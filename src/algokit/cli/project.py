import logging
import shutil
from pathlib import Path

import click

from algokit.core.project import (
    ProjectCommand,
    WorkspaceProjectCommand,
    load_commands,
    run_command,
    run_workspace_command,
)

logger = logging.getLogger(__name__)


def _load_custom_generate_commands(project_dir: Path) -> dict[str, click.Command]:
    """
    Load custom generate commands from .algokit.toml file.
    :param project_dir: Project directory path.
    :return: Custom generate commands.
    """

    custom_commands = load_commands(project_dir)
    commands_table: dict[str, click.Command] = {}

    for custom_command in custom_commands:

        @click.command(
            name=custom_command.name, help=custom_command.description or "Command description is not supplied."
        )
        def command(
            *,
            custom_command: ProjectCommand | WorkspaceProjectCommand = custom_command,  # Bind loop variable here
        ) -> None:
            if not shutil.which("git"):
                raise click.ClickException(
                    "Git not found; please install git and add to path.\n"
                    "See https://github.com/git-guides/install-git for more information."
                )

            # if not force and not click.confirm(
            #     "You are about to run a generator. Please make sure it's from a "
            #     "trusted source (for example, official AlgoKit Templates). Do you want to proceed?",
            #     default=False,
            # ):
            #     logger.warning("Generator execution cancelled.")
            #     return None

            return (
                run_command(custom_command)
                if isinstance(custom_command, ProjectCommand)
                else run_workspace_command(custom_command)
            )

        commands_table[custom_command.name] = command

    return commands_table


class ProjectGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return_value = super().get_command(ctx, cmd_name)

        if return_value is not None:
            return return_value

        commands = _load_custom_generate_commands(Path.cwd())
        return commands.get(cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        predefined_command_names = super().list_commands(ctx)
        dynamic_commands = _load_custom_generate_commands(Path.cwd())
        dynamic_command_names = list(dynamic_commands)

        return sorted(predefined_command_names + dynamic_command_names)


@click.group("project", cls=ProjectGroup)
def project_group() -> None:
    """Manage algokit projects."""
