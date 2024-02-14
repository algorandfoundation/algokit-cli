import dataclasses
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import click

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config
from algokit.core.proc import run

logger = logging.getLogger("rich")


@dataclasses.dataclass(kw_only=True)
class Generator:
    name: str
    path: str
    description: str | None = None


@dataclasses.dataclass(kw_only=True)
class ProjectCommand:
    name: str
    command: str
    cwd: str | None = None
    description: str | None = None


@dataclasses.dataclass(kw_only=True)
class ProjectDeployCommand(ProjectCommand):
    environment_secrets: list[str] | None = None
    command: list[str] | None = None


@dataclasses.dataclass(kw_only=True)
class WorkspaceProjectCommand:
    name: str
    description: str | None = None
    commands: list[ProjectCommand]  # List of paths where the command is found


def run_command(
    command: ProjectCommand,
) -> ProjectCommand:
    """
    Run the specified project command.
    :param command: The ProjectCommand instance to run.
    :param project_dir: Project directory path.
    """
    # Assuming command.command is a list of strings representing the command and its arguments
    result = run(
        command=command.command.split(" "),
        cwd=Path(command.cwd) if command.cwd else Path.cwd(),
        bad_return_code_error_message=f"Command {command.name} failed",
        stdout_log_level=logging.DEBUG,
    )

    if result.exit_code != 0:
        raise click.ClickException(f"Command {command.name} failed with exit code {result.exit_code}")

    return command


def run_workspace_command(workspace_command: WorkspaceProjectCommand) -> None:
    with ThreadPoolExecutor() as executor:
        futures = []
        for cmd in workspace_command.commands:
            # Extract the project name from the command's cwd path for logging
            project_name = Path(cmd.cwd).name if cmd.cwd else "Unknown Project"
            # Extract the command being executed for logging
            executed_command = cmd.command if cmd.command else "Unknown Command"
            # Log the command execution start
            logger.info(f"⏳ {project_name}: '{executed_command}' command in progress...")
            # Submit the command for execution
            future = executor.submit(run_command, cmd)
            futures.append(future)

        for future in as_completed(futures):
            try:
                result_cmd = future.result()  # You can handle results or exceptions here
                # Extract the project name from the command's cwd path
                project_name = Path(result_cmd.cwd).name if result_cmd.cwd else "Unknown Project"
                # Extract the command being executed
                executed_command = result_cmd.command if result_cmd.command else "Unknown Command"
                # Log the completion status
                logger.info(f"✅ {project_name}: '{executed_command}' command completed.")
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                raise e


def load_commands_from_standalone(config: dict[str, Any], project_dir: Path) -> list[ProjectCommand]:
    """
    Load the project commands for the given project from .algokit.toml file.
    :param project_dir: Project directory path.
    :return: List of ProjectCommand instances.
    """
    commands: list[ProjectCommand] = []
    if not config:
        return commands
    commands_table = config.get("project", {}).get("commands", {})

    if not isinstance(commands_table, dict):
        raise click.ClickException(f"Bad data for [project.commands] key in '{ALGOKIT_CONFIG}'")

    for name, command_config in commands_table.items():
        if name == "deploy":
            # Special handling for deploy commands using ProjectDeployCommand subclass
            environment_secrets = command_config.get("environment_secrets", None)
            command = command_config.get("command", None)
            description = command_config.get("description", None)
            deploy_command = ProjectDeployCommand(
                name=name,
                command=command.split() if isinstance(command, str) else command,
                description=description,
                environment_secrets=environment_secrets,
            )
            commands.append(deploy_command)
        else:
            # Default handling for other commands using ProjectCommand
            command = command_config.get("command", None)
            description = command_config.get("description", None)
            project_command = ProjectCommand(
                name=name,
                command=command,
                cwd=str(project_dir),
                description=description,
            )
            commands.append(project_command)

    return commands


def load_commands_from_workspace(config: dict[str, Any], project_dir: Path) -> list[WorkspaceProjectCommand]:  # noqa: C901
    commands_dict: dict[str, WorkspaceProjectCommand] = {}
    if not config:
        return list(commands_dict.values())

    def load_from_path(path: str) -> None:
        full_path = project_dir / path
        if not full_path.exists() or not full_path.is_dir():
            logger.warning(f"Path {full_path} does not exist or is not a directory")
            return

        for item in full_path.iterdir():
            if item.is_dir():
                dir_config = get_algokit_config(item)
                if dir_config:
                    standalone_commands = load_commands_from_standalone(dir_config, item)
                    for cmd in standalone_commands:
                        if cmd.name not in commands_dict:
                            commands_dict[cmd.name] = WorkspaceProjectCommand(
                                name=cmd.name,
                                description=f'Run all "{cmd.name}" commands in the project',
                                commands=[cmd],
                            )
                        else:
                            commands_dict[cmd.name].commands.append(cmd)

    projects_paths = config.get("project", {}).get("projects", [])

    if projects_paths:
        for projects_path in projects_paths:
            load_from_path(projects_path)

    # Convert each WorkspaceProjectCommand's commands list to have unique paths
    for wp_cmd in commands_dict.values():
        unique_paths = {str(cmd.cwd): cmd for cmd in wp_cmd.commands}
        wp_cmd.commands = list(unique_paths.values())

    return list(commands_dict.values())


def load_commands(project_dir: Path) -> list[ProjectCommand] | list[WorkspaceProjectCommand]:
    """
    Load the project commands for the given project from .algokit.toml file.
    :param project_dir: Project directory path.
    :return: List of ProjectCommand instances.
    """
    config = get_algokit_config(project_dir)

    if not config:
        return []

    return (
        load_commands_from_workspace(config, project_dir)
        if config.get("project", {}).get("type") == "workspace"
        else load_commands_from_standalone(config, project_dir)
    )
