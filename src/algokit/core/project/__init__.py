from enum import Enum
from pathlib import Path
from typing import Any

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config

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


def _get_project_root_dirs(config: dict[str, Any], project_dir: Path) -> list[Path]:
    """Retrieves a list of project root directories based on the provided project directory or the current working
    directory.

    This function searches for project directories within the specified root directory. It filters out directories that
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

    return [p for p in project_root_path.iterdir() if p.is_dir() and (p / ALGOKIT_CONFIG).exists()]


def get_algokit_project_configs(
    project_dir: Path | None = None, lookup_level: int = WORKSPACE_LOOKUP_LEVELS
) -> list[dict[str, Any]]:
    """Fetches configurations for all algokit projects within the specified directory or the current working directory.

    This function reads the .algokit.toml configuration file from each project directory and returns a list of
    dictionaries, each representing a project's configuration.

    Args:
        project_dir (Path | None): The base directory to search for project configurations. If None, the current
        working directory is used.
        lookup_level (int): The number of levels to go up the directory to search for workspace projects

    Returns:
        list[dict[str, Any] | None]: A list of dictionaries, each containing the configuration of an algokit project.
        Returns None for projects where the configuration could not be read.
    """

    if lookup_level < 0:
        raise FileNotFoundError("Could not find any workspace projects")

    project_dir = project_dir or Path.cwd()
    project_config = get_algokit_config(project_dir=project_dir)

    if not project_config:
        return get_algokit_project_configs(project_dir=project_dir.parent, lookup_level=lookup_level - 1)

    configs = []

    for sub_project_dir in _get_project_root_dirs(project_config, project_dir):
        config = get_algokit_config(project_dir=sub_project_dir)
        if config is not None:
            config["cwd"] = sub_project_dir
            configs.append(config)

    return (
        configs
        if configs
        else get_algokit_project_configs(project_dir=project_dir.parent, lookup_level=lookup_level - 1)
    )


def get_algokit_projects_names_from_workspace(project_dir: Path | None = None) -> list[str]:
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

    project_dirs = _get_project_root_dirs(config, project_dir)
    return [p.name for p in project_dirs]
