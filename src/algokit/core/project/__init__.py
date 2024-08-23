from enum import Enum
from functools import cache
from pathlib import Path
from typing import Any

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config
from algokit.core.utils import alphanumeric_sort_key

WORKSPACE_LOOKUP_LEVELS = 2


class ProjectType(str, Enum):
    """
    Enum class for specifying the type of algokit projects.

    Attributes:
        WORKSPACE (str): Represents a workspace project type.
        BACKEND (str): Represents a backend project type, typically for server-side operations.
        FRONTEND (str): Represents a frontend project type, typically for client-side operations.
        CONTRACT (str): Represents a contract project type, typically for blockchain contracts.
    """

    WORKSPACE = "workspace"
    BACKEND = "backend"
    FRONTEND = "frontend"
    CONTRACT = "contract"


def _get_subprojects_paths(config: dict[str, Any], project_dir: Path) -> list[Path]:
    """Searches for project directories within the specified workspace. It filters out directories that
    do not contain an algokit configuration file.

    Args:
        config (dict[str, Any]): The configuration of the project.
        working directory is used.
        project_dir (Path): The base directory to search for project root directories. If None, the current
        working directory is used.

    Returns:
        list[Path]: A list containing paths to project root directories that contain an algokit configuration file.
    """

    projects_root = config.get("project", {}).get("projects_root_path", None)
    if projects_root is None:
        return []

    project_root_path = project_dir / projects_root

    if not project_root_path.exists():
        return []

    return [
        sub_project
        for sub_project in project_root_path.iterdir()
        if sub_project.is_dir() and (sub_project / ALGOKIT_CONFIG).exists()
    ]


@cache
def get_project_configs(
    project_dir: Path | None = None,
    lookup_level: int = WORKSPACE_LOOKUP_LEVELS,
    project_type: str | None = None,
    project_names: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Recursively finds configurations for all algokit projects within the specified directory or the
    current working directory.

    This function reads the .algokit.toml configuration file from each project directory and returns a list of
    dictionaries, each representing a project's configuration. Additionally appends 'cwd' at the root of each dict
    object loa

    Args:
        project_dir (Path | None): The base directory to search for project configurations. If None, the current
        working directory is used.
        lookup_level (int): The number of levels to go up the directory to search for workspace projects
        project_type (str | None): The type of project to filter by. If None, all project types are returned.
        project_names (tuple[str, ...] | None): The names of the projects to filter by. If None, gets all projects.

    Returns:
        list[dict[str, Any] | None]: A list of dictionaries, each containing the configuration of an algokit project.
        Returns None for projects where the configuration could not be read.
    """

    if lookup_level < 0:
        return []

    project_dir = project_dir or Path.cwd()
    project_config = get_algokit_config(project_dir=project_dir)

    if not project_config:
        return get_project_configs(
            project_dir=project_dir.parent,
            lookup_level=lookup_level - 1,
            project_type=project_type,
            project_names=project_names,
        )

    configs = []
    for sub_project_dir in _get_subprojects_paths(project_config, project_dir):
        config = get_algokit_config(project_dir=sub_project_dir) or {}
        type_mismatch = project_type and config.get("project", {}).get("type") != project_type
        name_mismatch = project_names and config.get("project", {}).get("name") not in project_names
        if not type_mismatch and not name_mismatch:
            config["cwd"] = sub_project_dir
            configs.append(config)

    # Sort configs by the directory name alphanumerically
    sorted_configs = sorted(configs, key=lambda x: alphanumeric_sort_key(x["cwd"].name))

    return (
        sorted_configs
        if sorted_configs
        else get_project_configs(
            project_dir=project_dir.parent,
            lookup_level=lookup_level - 1,
            project_type=project_type,
            project_names=project_names,
        )
    )


@cache
def get_project_dir_names_from_workspace(project_dir: Path | None = None) -> list[str]:
    """
    Generates a list of project names from the .algokit.toml file within the specified directory or the current
    working directory.

    This function is useful for identifying all the projects within a given workspace by their names.

    Args:
        project_dir (Path | None): The base directory to search for project names. If None,
        the current working directory is used.

    Returns:
        list[str]: A list of project names found within the specified directory.
    """

    project_dir = project_dir or Path.cwd()
    config = get_algokit_config(project_dir=project_dir)

    if not config:
        return []

    return [p.name for p in _get_subprojects_paths(config, project_dir)]


def get_workspace_project_path(
    project_dir: Path | None = None, lookup_level: int = WORKSPACE_LOOKUP_LEVELS
) -> Path | None:
    """Recursively searches for the workspace project path within the specified directory.

    Args:
        project_dir (Path): The base directory to search for the workspace project path.
        lookup_level (int): The number of levels to go up the directory to search for workspace projects.

    Returns:
        Path | None: The path to the workspace project directory or None if not found.
    """

    if lookup_level < 0:
        return None

    project_dir = project_dir or Path.cwd()
    project_config = get_algokit_config(project_dir=project_dir)

    if not project_config or project_config.get("project", {}).get("type") != ProjectType.WORKSPACE:
        return get_workspace_project_path(project_dir=project_dir.parent, lookup_level=lookup_level - 1)

    return project_dir
