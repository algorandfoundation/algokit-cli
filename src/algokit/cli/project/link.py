import logging
import typing
from dataclasses import dataclass
from pathlib import Path

import click
import questionary

from algokit.cli.common.utils import MutuallyExclusiveOption
from algokit.core import questionary_extensions
from algokit.core.conf import get_algokit_config
from algokit.core.project import ProjectType, get_project_configs
from algokit.core.typed_client_generation import ClientGenerator

logger = logging.getLogger(__name__)


@dataclass
class ContractArtifacts:
    """Represents the contract project artifacts.

    Attributes:
        project_name (str): The name of the project.
        cwd (Path): The current working directory of the project.
    """

    project_name: str
    cwd: Path


def _is_frontend(project_data: dict) -> bool:
    """Determines if the project is a frontend project.

    Args:
        project_data (dict): The project data to evaluate.

    Returns:
        bool: True if the project is a frontend project, False otherwise.
    """
    return project_data.get("type") == ProjectType.FRONTEND


def _get_contract_projects() -> list[ContractArtifacts]:
    """Retrieves contract projects configurations.

    Returns:
        list[ContractArtifacts]: A list of contract project artifacts.
    """
    contract_configs = []
    try:
        project_configs = get_project_configs(project_type="contract")
        for config in project_configs:
            project = config.get("project", {})
            project_type = project.get("type")
            project_name = project.get("name")
            project_cwd = config.get("cwd", Path.cwd())
            contract_artifacts = project.get("artifacts")

            if any([not project_type, not project_name, not project_cwd, not contract_artifacts]):
                continue

            contract_configs.append(ContractArtifacts(project_name, project_cwd))

        return contract_configs
    except Exception:
        return []


def _link_projects(
    *,
    frontend_clients_path: Path,
    contract_project_root: Path,
    language: str,
    fail_fast: bool,
    version: str | None = None,
) -> None:
    """Links projects by generating client code.

    Args:
        frontend_clients_path (Path): The path to the frontend clients.
        contract_project_root (Path): The root path of the contract project.
        language (str): The programming language of the generated client code.
        fail_fast (bool): Whether to exit immediately if a client generation process fails.
        version (str | None): Version to pin the client generator to (Defaults to None).
    """
    output_path_pattern = f"{frontend_clients_path}/{{contract_name}}.{'ts' if language == 'typescript' else 'py'}"
    generator = ClientGenerator.create_for_language(language, version=version)
    app_specs = list(contract_project_root.rglob("application.json")) + list(
        contract_project_root.rglob("*.arc32.json")
    )
    if not app_specs:
        click.secho(
            f"WARNING: No application.json | *.arc32.json files found in {contract_project_root}. Skipping...",
            fg="yellow",
        )
        return

    for app_spec in app_specs:
        output_path = generator.resolve_output_path(app_spec, output_path_pattern)
        if output_path is None:
            if fail_fast:
                raise click.ClickException(f"Error generating client for {app_spec}")

            logger.warning(f"Error generating client for {app_spec}")
            continue
        generator.generate(app_spec, output_path)


def _prompt_contract_project() -> ContractArtifacts | None:
    """Prompts the user to select a contract project.

    Returns:
        ContractArtifacts | None: The selected contract project artifacts or None if no projects are available.
    """
    contract_projects = _get_contract_projects()

    if not contract_projects:
        return None

    return typing.cast(
        ContractArtifacts,
        questionary_extensions.prompt_select(
            "Select contract project to link with",
            *[questionary.Choice(title=contract.project_name, value=contract) for contract in contract_projects],
        ),
    )


def _select_contract_projects_to_link(
    *,
    project_names: typing.Sequence[str] | None = None,
    link_all: bool = False,
) -> list[ContractArtifacts]:
    """Selects contract projects to link based on criteria.

    Args:
        project_names (typing.Sequence[str] | None): Specific project names to link. Defaults to None.
        link_all (bool): Whether to link all projects. Defaults to False.

    Returns:
        list[ContractArtifacts]: A list of contract project artifacts to link.
    """
    if link_all:
        return _get_contract_projects()
    elif project_names:
        return [project for project in _get_contract_projects() if project.project_name in project_names]
    else:
        contract_project = _prompt_contract_project()
        return [contract_project] if contract_project else []


@click.command("link")
@click.option(
    "project_names",
    "--project-name",
    "-p",
    multiple=True,
    help="Specify contract projects for the command. Defaults to all in the current workspace.",
    nargs=1,
    default=[],
    metavar="<value>",
    required=False,
)
@click.option(
    "--language",
    "-l",
    default="typescript",
    type=click.Choice(ClientGenerator.languages()),
    help="Programming language of the generated client code",
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
@click.option(
    "fail_fast",
    "--fail-fast",
    "-f",
    help="Exit immediately if at least one client generation process fails",
    default=False,
    is_flag=True,
    type=click.BOOL,
    required=False,
)
@click.option(
    "--version",
    "-v",
    "version",
    default=None,
    help="The client generator version to pin to, for example, 1.0.0. "
    "If no version is specified, AlgoKit checks if the client generator is installed and runs the installed version. "
    "If the client generator is not installed, AlgoKit runs the latest version. "
    "If a version is specified, AlgoKit checks if an installed version matches and runs the installed version. "
    "Otherwise, AlgoKit runs the specified version.",
)
def link_command(
    *, project_names: tuple[str] | None, language: str, link_all: bool, fail_fast: bool, version: str | None
) -> None:
    """Automatically invoke 'algokit generate client' on contract projects available in the workspace.
    Must be invoked from the root of a standalone 'frontend' typed project."""

    config = get_algokit_config() or {}
    project_data = config.get("project", {})

    if not config:
        click.secho("WARNING: No .algokit.toml config found. Skipping...", fg="yellow")
        return

    if not _is_frontend(project_data):
        click.secho("WARNING: This command is only available in projects of type `frontend`. Skipping...", fg="yellow")
        return

    frontend_artifacts_path = project_data.get("artifacts")
    if not frontend_artifacts_path:
        raise click.ClickException("No `contract_clients` path specified in .algokit.toml")

    contract_projects = _select_contract_projects_to_link(
        project_names=project_names,
        link_all=link_all,
    )

    if not contract_projects:
        click.secho(
            f"WARNING: No {' '.join(project_names) if project_names else 'contract project(s)'} found. Skipping...",
            fg="yellow",
        )
        return

    iteration = 1
    total = len(contract_projects)
    for contract_project in contract_projects:
        _link_projects(
            frontend_clients_path=Path.cwd() / frontend_artifacts_path,
            contract_project_root=contract_project.cwd,
            language=language,
            fail_fast=fail_fast,
            version=version,
        )

        logger.info(f"✅ {iteration}/{total}: Finished processing {contract_project.project_name}")
        iteration += 1
