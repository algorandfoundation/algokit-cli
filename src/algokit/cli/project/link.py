import logging
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import click
import questionary

from algokit.cli.common.utils import MutuallyExclusiveOption
from algokit.core import proc, questionary_extensions
from algokit.core.conf import get_algokit_config
from algokit.core.init import ProjectType
from algokit.core.project import get_algokit_project_configs

logger = logging.getLogger(__name__)


@dataclass
class ContractArtifacts:
    project_name: str
    cwd: Path


def _get_project_data() -> dict:
    config = get_algokit_config()
    if not config:
        raise click.ClickException("No .algokit.toml config found.")
    return config.get("project", {})


def _is_frontend(project_data: dict) -> bool:
    return project_data.get("type") == ProjectType.FRONTEND


@cache
def _get_contract_projects() -> list[ContractArtifacts]:
    contract_configs = []
    try:
        project_configs = get_algokit_project_configs()
        for config in project_configs:
            project = config.get("project", {})
            project_type = project.get("type")
            project_name = project.get("name")
            project_cwd = config.get("cwd", Path.cwd())
            contract_artifacts = project.get("artifacts")

            # if any of the above are none then continue
            if any([not project_type, not project_name, not project_cwd, not contract_artifacts]):
                continue

            if project_type == ProjectType.CONTRACT:
                contract_configs.append(ContractArtifacts(project_name, project_cwd))

        return contract_configs
    except Exception:
        return []


@cache
def _get_contract_project(project_name: str) -> ContractArtifacts:
    return next(filter(lambda x: x.project_name == project_name, _get_contract_projects()))


def _link_projects(frontend_clients_path: Path, contract_project_root: Path) -> None:
    frontend_output_argument = f"-o {frontend_clients_path}/" + "{contract_name}.ts"
    link_command = f"algokit generate client {frontend_output_argument} {contract_project_root}".split()

    result = proc.run(link_command)
    if result.exit_code != 0:
        raise click.ClickException(
            f"Generating typed clients at {contract_project_root} exited with exit code {result.exit_code}"
        )


def _prompt_contract_project() -> ContractArtifacts:
    return questionary_extensions.prompt_select(
        "Select contract project to link with",
        *[
            questionary.Choice(title=contract.project_name, value=contract) for contract in _get_contract_projects()
        ],  # Modified line
    )


@click.command("link")
@click.option(
    "--project_name",
    "-p",
    "project_name",
    type=click.STRING,
    required=False,
    help=(
        "(Optional) Name of the contract project to link with the frontend project. "
        "If not specified, will prompt the user to select from the available contract projects."
    ),
    cls=MutuallyExclusiveOption,
    not_required_if=["link_all"],
)
@click.option(
    "link_all",
    "--all",
    "-a",
    help="Link all contract projects with the frontend project",
    default=False,
    is_flag=True,
    type=click.BOOL,
    required=False,
    cls=MutuallyExclusiveOption,
    not_required_if=["project_name"],
)
def link_command(*, project_name: str | None, link_all: bool = False) -> None:
    """Link contract projects with the frontend project"""

    contract_projects = []
    if link_all:
        contract_projects = _get_contract_projects()
    else:
        contract_projects = [_prompt_contract_project() if not project_name else _get_contract_project(project_name)]

    if not contract_projects:
        raise click.ClickException("No contract project selected or found")

    """Automatically export typed clients from contract projects into frontends (if any)."""
    project_data = _get_project_data()

    if not _is_frontend(project_data):
        raise click.ClickException("This command is only available in a standalone frontend projects.")

    frontend_artifacts_path = project_data.get("artifacts")
    if not frontend_artifacts_path:
        raise click.ClickException("No `contract_clients` path specified in .algokit.toml")

    iteration = 1
    total = len(contract_projects)
    for contract_project in contract_projects:
        _link_projects(Path.cwd() / frontend_artifacts_path, contract_project.cwd)

        click.echo(
            f"✅ {iteration}/{total}: Exported typed clients from "
            f"{contract_project.project_name} typed clients to {frontend_artifacts_path}"
        )
        iteration += 1
