from enum import Enum
from pathlib import Path

from algokit.core.conf import get_algokit_config


class ProjectType(str, Enum):
    """
    Enum for holding types of algokit projects
    """

    WORKSPACE = "workspace"
    BACKEND = "backend"
    FRONTEND = "frontend"
    CONTRACT = "contract"


def get_algokit_projects_from_config(project_dir: Path | None = None) -> list[str]:
    """
    Get the list of projects from the .algokit.toml file.
    :return: List of project names in a list.
    """
    config = get_algokit_config(project_dir=project_dir or Path.cwd())
    if config is None:
        return []

    project_root = config.get("project", {}).get("projects_root_path", None)
    if project_root is None:
        return []

    project_root = Path(project_root)
    if not project_root.exists():
        return []

    return [p.name for p in Path(project_root).iterdir() if p.is_dir()]
