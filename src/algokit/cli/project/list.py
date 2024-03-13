import logging
from pathlib import Path

import click

from algokit.core.conf import get_algokit_config
from algokit.core.project import ProjectType, get_project_configs

logger = logging.getLogger(__name__)


PROJECT_TYPE_TO_ICON = {
    ProjectType.CONTRACT: "📜",
    ProjectType.FRONTEND: "🖥️",
    ProjectType.WORKSPACE: "📁",
    ProjectType.BACKEND: "⚙️",
}


def _is_workspace(workspace_path: Path | None = None) -> bool:
    config = get_algokit_config(project_dir=workspace_path) or {}
    project = config.get("project", {})
    return bool(project.get("type", None) == ProjectType.WORKSPACE)


@click.command("list")
@click.argument(
    "workspace_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path),
    default=".",
)
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose output")
def list_command(*, workspace_path: Path, verbose: bool) -> None:
    """List all projects in the workspace"""

    if not _is_workspace(workspace_path):
        click.secho(
            "WARNING: No AlgoKit workspace found. Check [project.type] definition at .algokit.toml",
            fg="yellow",
            err=True,
        )
        return

    configs = get_project_configs(workspace_path)

    if not configs:
        click.secho(
            "WARNING: No AlgoKit project(s) found in the workspace. Check [project.type] definition at .algokit.toml",
            fg="yellow",
            err=True,
        )
        return

    for config in configs:
        project = config.get("project", {})
        name, project_type = project.get("name"), project.get("type")
        cwd = f": ({config.get('cwd')})" if verbose else ""
        click.echo(f"{name}{cwd} {PROJECT_TYPE_TO_ICON[project_type]}")
