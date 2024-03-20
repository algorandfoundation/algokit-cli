import logging
from pathlib import Path

import click

from algokit.core.conf import get_algokit_config
from algokit.core.project import ProjectType, get_project_configs, get_workspace_project_path

logger = logging.getLogger(__name__)


PROJECT_TYPE_ICONS = {
    ProjectType.CONTRACT: "📜",
    ProjectType.FRONTEND: "🖥️",
    ProjectType.WORKSPACE: "📁",
    ProjectType.BACKEND: "⚙️",
}


def _is_workspace(workspace_path: Path | None = None) -> bool:
    config = get_algokit_config(project_dir=get_workspace_project_path(workspace_path)) or {}
    project = config.get("project", {})
    return bool(project.get("type", None) == ProjectType.WORKSPACE)


@click.command("list")
@click.argument(
    "workspace_path",
    type=click.Path(exists=True, resolve_path=True, file_okay=False, dir_okay=True, readable=True, path_type=Path),
    default=".",
)
def list_command(*, workspace_path: Path) -> None:
    """List all projects in the workspace"""

    is_workspace = True
    resolved_workspace_path = get_workspace_project_path(workspace_path)
    if resolved_workspace_path is None:
        is_workspace = False

    if not is_workspace:
        click.secho(
            "WARNING: No AlgoKit workspace found. Check [project.type] definition at .algokit.toml",
            fg="yellow",
            err=True,
        )
        return

    configs = get_project_configs(resolved_workspace_path)

    if not configs:
        click.secho(
            "WARNING: No AlgoKit project(s) found in the workspace. Check [project.type] definition at .algokit.toml",
            fg="yellow",
            err=True,
        )
        return

    click.echo(f"workspace: {resolved_workspace_path} {PROJECT_TYPE_ICONS[ProjectType.WORKSPACE]}")
    for config in configs:
        project = config.get("project", {})
        name, project_type = project.get("name"), project.get("type")
        cwd = Path(config.get("cwd", Path.cwd()))
        path_label = "this directory" if cwd == Path.cwd() else cwd
        icon = PROJECT_TYPE_ICONS.get(project_type, "🔍 Unknown")
        click.echo(f"  - {name} ({path_label}) {icon}")
