import dataclasses
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import click

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config
from algokit.core.proc import run
from algokit.core.project import ProjectType
from algokit.core.utils import (
    load_env_file,
    resolve_command_path,
    split_command_string,
)

logger = logging.getLogger("rich")


@dataclasses.dataclass(kw_only=True)
class ProjectCommand:
    """Represents a command to be executed within a project context.

    Attributes:
        name (str): The name of the command.
        command (list[str]): The command to be executed, as a list of strings.
        cwd (Path | None): The current working directory from which the command should be executed.
        description (str | None): A brief description of the command.
        project_name (str): The name of the project associated with this command.
    """

    name: str
    project_type: str
    commands: list[list[str]]
    cwd: Path | None = None
    description: str | None = None
    project_name: str
    env_file: Path | None


@dataclasses.dataclass(kw_only=True)
class WorkspaceProjectCommand:
    """Represents a command that encompasses multiple project commands within a workspace.

    Attributes:
        name (str): The name of the workspace command.
        description (str | None): A brief description of the workspace command.
        commands (list[ProjectCommand]): A list of `ProjectCommand` instances to be executed.
        execution_order (list[str]): The order in which the commands should be executed.
    """

    name: str
    description: str | None = None
    commands: list[ProjectCommand]
    execution_order: list[str]


def _load_commands_from_standalone(
    config: dict[str, Any],
    project_dir: Path,
) -> list[ProjectCommand]:
    """Loads commands for standalone projects based on the project configuration.

    Args:
        config (dict[str, Any]): The project configuration.
        project_dir (Path): The directory of the project.

    Returns:
        list[ProjectCommand]: A list of project commands derived from the configuration.

    Raises:
        click.ClickException: If the project configuration is invalid.
    """
    commands: list[ProjectCommand] = []
    project_config = config.get("project", {})
    project_commands = project_config.get("run", {})
    project_name = project_config.get("name")  # Ensure name is present
    project_type = project_config.get("type")

    if not project_name:
        raise click.ClickException(
            "Project name is required in the .algokit.toml file for projects of type 'contract', 'backend' or 'frontend"
        )

    if not isinstance(project_commands, dict):
        raise click.ClickException(f"Bad data for [project.commands] key in '{ALGOKIT_CONFIG}'")

    for name, command_config in project_commands.items():
        raw_commands = command_config.get("commands")
        description = command_config.get("description", "Description not available")
        raw_env_file = command_config.get("env_file", None)
        env_file = Path(raw_env_file) if raw_env_file else None

        if not raw_commands:
            logger.debug(f"Command '{name}' has no custom commands to execute, skipping...")
            continue

        commands.append(
            ProjectCommand(
                name=name,
                commands=[split_command_string(cmd) for cmd in raw_commands],
                cwd=project_dir,  # Assumed to be Path object
                description=description,
                project_name=project_name,
                env_file=env_file,
                project_type=project_type,
            )
        )

    return commands


def _load_commands_from_workspace(
    config: dict[str, Any],
    project_dir: Path,
) -> list[WorkspaceProjectCommand]:
    """Loads workspace commands based on the workspace configuration.

    Args:
        config (dict[str, Any]): The workspace configuration.
        project_dir (Path): The directory of the workspace.

    Returns:
        list[WorkspaceProjectCommand]: A list of workspace project commands derived from the configuration.
    """
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

    for subproject_dir in sorted(sub_projects_root_dir.iterdir(), key=lambda p: p.name):
        if not subproject_dir.is_dir():
            continue

        subproject_config = get_algokit_config(project_dir=subproject_dir, verbose_validation=True)
        if not subproject_config:
            continue

        standalone_commands = _load_commands_from_standalone(subproject_config, subproject_dir)

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


def run_command(
    *, command: ProjectCommand, from_workspace: bool = False, extra_args: tuple[str, ...] | None = None
) -> None:
    """Executes a specified project command.

    Args:
        command (ProjectCommand): The project command to be executed.
        from_workspace (bool): Indicates whether the command is being executed from a workspace context.
        extra_args (tuple[str, ...] | None): Optional; additional arguments to pass to the command.

    Raises:
        click.ClickException: If the command execution fails.
    """
    is_verbose = not from_workspace or logger.level == logging.DEBUG

    if is_verbose:
        logger.info(f"Running `{command.name}` command in {command.cwd}...")

    config_dotenv = (
        load_env_file(command.env_file) if command.env_file else load_env_file(command.cwd) if command.cwd else {}
    )
    # environment variables take precedence over those in .env* files
    config_env = {**{k: v for k, v in config_dotenv.items() if v is not None}, **os.environ}

    for index, cmd in enumerate(command.commands):
        try:
            resolved_command = resolve_command_path(cmd)
            if index == len(command.commands) - 1 and extra_args:
                resolved_command.extend(extra_args)
        except click.ClickException as e:
            logger.error(f"'{command.name}' failed executing: '{' '.join(cmd)}'")
            raise e

        result = run(
            command=resolved_command,
            cwd=command.cwd,
            env=config_env,
            stdout_log_level=logging.DEBUG,
        )

        if result.exit_code != 0:
            header = f" project run '{command.name}' command output: ".center(80, "·")
            logger.error(f"\n{header}\n{result.output}")
            raise click.ClickException(
                f"'{command.name}' failed executing '{' '.join(cmd)}' with exit code = {result.exit_code}"
            )

        # Log after each command if not from workspace, and also log success after the last command
        if is_verbose:
            log_msg = f"Command Executed: '{' '.join(cmd)}'\nOutput: {result.output}\n"
            if index == len(command.commands) - 1:
                if extra_args:
                    log_msg += f"Extra Args: '{' '.join(extra_args)}'\n"
                log_msg += f"✅ {command.project_name}: '{' '.join(cmd)}' executed successfully."
            logger.info(log_msg)


def run_workspace_command(
    *,
    workspace_command: WorkspaceProjectCommand,
    project_names: list[str] | None = None,
    project_type: str | None = None,
    sequential: bool = False,
    extra_args: tuple[str, ...] | None = None,
) -> None:
    """Executes a workspace command, potentially limited to specified projects.

    Args:
        workspace_command (WorkspaceProjectCommand): The workspace command to be executed.
        project_names (list[str] | None): Optional; specifies a subset of projects to execute the command for.
        project_type (str | None): Optional; specifies a subset of project types to execute the command for.
        sequential (bool): Whether to execute commands sequentially. Defaults to False.
        extra_args (tuple[str, ...] | None): Optional; additional arguments to pass to the command.
    """

    def _execute_command(cmd: ProjectCommand) -> None:
        """Helper function to execute a single project command within the workspace context."""
        logger.info(f"⏳ {cmd.project_name}: '{cmd.name}' command in progress...")
        try:
            run_command(command=cmd, from_workspace=True, extra_args=extra_args or ())
            executed_commands = " && ".join(" ".join(command) for command in cmd.commands)
            if extra_args:
                executed_commands += f" {' '.join(extra_args)}"
            logger.info(f"✅ {cmd.project_name}: '{executed_commands}' executed successfully.")
        except Exception as e:
            logger.error(f"❌ {cmd.project_name}: {e}")
            raise click.ClickException(f"failed to execute '{cmd.name}' command in '{cmd.project_name}'") from e

    def _filter_command(cmd: ProjectCommand) -> bool:
        return (not project_names or cmd.project_name in project_names) and (
            not project_type or project_type == cmd.project_type
        )

    is_sequential = workspace_command.execution_order or sequential
    logger.info(f"Running commands {'sequentially' if is_sequential else 'concurrently'}.")

    filtered_commands = list(filter(_filter_command, workspace_command.commands))

    if project_names:
        existing_projects = {cmd.project_name for cmd in filtered_commands}
        missing_projects = set(project_names) - existing_projects
        if missing_projects:
            logger.warning(f"Missing projects: {', '.join(missing_projects)}. Proceeding with available ones.")

    if is_sequential:
        if workspace_command.execution_order:
            order_map = {name: i for i, name in enumerate(workspace_command.execution_order)}
            filtered_commands.sort(key=lambda c: order_map.get(c.project_name, len(order_map)))

        for cmd in filtered_commands:
            _execute_command(cmd)
    else:
        with ThreadPoolExecutor() as executor:
            list(executor.map(_execute_command, filtered_commands))


def load_commands(project_dir: Path) -> list[ProjectCommand] | list[WorkspaceProjectCommand] | None:
    """Determines and loads the appropriate project commands based on the project type.

    Args:
        project_dir (Path): The directory of the project.

    Returns:
        list[ProjectCommand] | list[WorkspaceProjectCommand] | None: A list of project or workspace commands,
        or None if the project configuration is not found.
    """
    config = get_algokit_config(project_dir=project_dir, verbose_validation=True)
    if not config:
        return None

    project_type = config.get("project", {}).get("type")
    return (
        _load_commands_from_workspace(config, project_dir)
        if project_type == ProjectType.WORKSPACE
        else _load_commands_from_standalone(config, project_dir)
    )
