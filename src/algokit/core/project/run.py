import dataclasses
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import click

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config
from algokit.core.proc import run
from algokit.core.project import ProjectType
from algokit.core.utils import resolve_command_path, split_command_string

logger = logging.getLogger("rich")


@dataclasses.dataclass(kw_only=True)
class ProjectCommand:
    name: str
    command: list[str]
    cwd: Path | None = None
    description: str | None = None
    project_name: str


@dataclasses.dataclass(kw_only=True)
class WorkspaceProjectCommand:
    name: str
    description: str | None = None
    commands: list[ProjectCommand]
    execution_order: list[str]


def run_command(*, command: ProjectCommand, from_workspace: bool = False) -> None:
    """Encapsulates the execution of a single project command"""
    result = run(
        command=command.command,
        cwd=command.cwd,
        stdout_log_level=logging.DEBUG,
    )

    if result.exit_code != 0:
        logger.error(result.output)
        raise click.ClickException(f"Command {command.name} failed with exit code {result.exit_code}")

    if not from_workspace:
        logger.info(result.output)
        logger.info(f"✅ {command.project_name}: '{' '.join(command.command)}' executed successfully.")


def run_workspace_command(
    workspace_command: WorkspaceProjectCommand,
    project_names: list[str] | None = None,
) -> None:
    def _execute_command(cmd: ProjectCommand) -> None:  # Nested for clarity
        logger.info(f"⏳ {cmd.project_name}: '{cmd.name}' command in progress...")
        try:
            run_command(command=cmd, from_workspace=True)
            logger.info(f"✅ {cmd.project_name}: '{' '.join(cmd.command)}' executed successfully.")
        except Exception as e:
            logger.error(f"❌ {cmd.project_name}: execution failed: {e}")
            raise e

    if workspace_command.execution_order:
        logger.info("Detected execution order, running commands sequentially")
        order_map = {name: i for i, name in enumerate(workspace_command.execution_order)}
        sorted_commands = sorted(
            workspace_command.commands, key=lambda c: order_map.get(c.project_name, len(order_map))
        )

        # Check if any project_names match the existing projects in the workspace
        if project_names and not any(cmd.project_name in project_names for cmd in sorted_commands):
            logger.warning("None of the specified project names exist in the workspace. Skipping execution.")
            return

        for cmd in sorted_commands:
            if project_names and cmd.project_name not in project_names:
                continue
            _execute_command(cmd)
    else:
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(_execute_command, cmd): cmd for cmd in workspace_command.commands}
            for future in as_completed(futures):
                future.result()


def load_commands_from_standalone(
    config: dict[str, Any],
    project_dir: Path,
) -> list[ProjectCommand]:
    """Loads commands for standalone projects (backend, frontend, etc.)"""
    commands: list[ProjectCommand] = []
    project_config = config.get("project", {})
    project_commands = project_config.get("run", {})
    project_name = project_config.get("name")  # Ensure name is present

    if not project_name:
        raise click.ClickException(
            "Project name is required in the .algokit.toml file for projects of type 'contract', 'backend' or 'frontend"
        )

    if not isinstance(project_commands, dict):
        raise click.ClickException(f"Bad data for [project.commands] key in '{ALGOKIT_CONFIG}'")

    for name, command_config in project_commands.items():
        raw_command = command_config.get("command")
        description = command_config.get("description", "Description not available")

        if not raw_command:
            logger.warning(f"Command '{name}' has no command, skipping...")
            continue

        commands.append(
            ProjectCommand(
                name=name,
                command=resolve_command_path(split_command_string(raw_command)),
                cwd=project_dir,  # Assumed to be Path object
                description=description,
                project_name=project_name,
            )
        )

    return commands


def load_commands_from_workspace(
    config: dict[str, Any],
    project_dir: Path,
) -> list[WorkspaceProjectCommand]:
    """Loads commands from a workspace configuration"""
    workspace_commands: dict[str, WorkspaceProjectCommand] = {}
    execution_order = config.get("project", {}).get("run", {})
    sub_projects_root = config.get("project", {}).get("projects_root_path")

    if not sub_projects_root:
        logger.warning("Missing 'projects_root_path' in workspace config; skipping command loading")
        return []

    sub_projects_root_dir = project_dir / sub_projects_root
    if not sub_projects_root_dir.exists() or not sub_projects_root_dir.is_dir():
        logger.warning(f"Path {sub_projects_root_dir} does not exist or is not a directory, skipping...")
        return []

    for subproject_dir in sub_projects_root_dir.iterdir():
        if not subproject_dir.is_dir():
            continue

        subproject_config = get_algokit_config(subproject_dir)
        if not subproject_config:
            continue

        standalone_commands = load_commands_from_standalone(subproject_config, subproject_dir)

        for standalone_cmd in standalone_commands:
            if standalone_cmd.name not in workspace_commands:
                workspace_commands[standalone_cmd.name] = WorkspaceProjectCommand(
                    name=standalone_cmd.name,
                    description=f'Run all "{standalone_cmd.name}" commands in the workspace project.',
                    commands=[standalone_cmd],
                    execution_order=execution_order.get(standalone_cmd.name, []),
                )
            else:
                workspace_commands[standalone_cmd.name].commands.append(standalone_cmd)

    return list(workspace_commands.values())


def load_commands(project_dir: Path) -> list[ProjectCommand] | list[WorkspaceProjectCommand] | None:
    """Loads project commands based on the project's type"""
    config = get_algokit_config(project_dir)
    if not config:
        return None

    project_type = config.get("project", {}).get("type")
    return (
        load_commands_from_workspace(config, project_dir)
        if project_type == ProjectType.WORKSPACE
        else load_commands_from_standalone(config, project_dir)
    )
