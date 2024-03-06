import logging

import click

from algokit.core.conf import get_algokit_config
from algokit.core.project import ProjectType, get_algokit_projects_names_from_workspace

logger = logging.getLogger(__name__)


def _is_workspace() -> bool:
    config = get_algokit_config() or {}
    project = config.get("project", {})
    return project.get("type", None) == ProjectType.WORKSPACE


@click.command("list", hidden=not _is_workspace())
def list_command() -> None:
    """List all projects in the workspace"""

    if not _is_workspace():
        raise click.ClickException("This command is only available in a workspace.")

    project_names = get_algokit_projects_names_from_workspace()

    for project_name in project_names:
        click.echo(f"ℹ️  {project_name}")  # noqa: RUF001
