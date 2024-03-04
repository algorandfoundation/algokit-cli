from collections.abc import Callable
from pathlib import Path
from typing import List, Dict

import pytest
from _pytest.tmpdir import TempPathFactory

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke

DirWithAppSpecFactory = Callable[[Path], Path]


def _create_project_config(
    project_dir: Path, project_type: str, project_name: str, command: str, description: str
) -> None:
    """
    Creates a .algokit.toml configuration file for a project.
    """
    project_config = f"""
[project]
type = '{project_type}'
name = '{project_name}'

[project.run]
hello = {{ command = '{command}', description = '{description}' }}
    """.strip()
    (project_dir / ".algokit.toml").write_text(project_config, encoding="utf-8")


def _create_workspace_project(workspace_dir: Path, projects: List[Dict[str, str]]) -> None:
    """
    Creates a workspace project and its subprojects.
    """
    workspace_dir.mkdir()
    (workspace_dir / ".algokit.toml").write_text(
        """
[project]
type = 'workspace'
projects_root_path = 'projects'

[project.run]
hello = ['contract_project', 'frontend_project']
        """.strip(),
        encoding="utf-8",
    )
    (workspace_dir / "projects").mkdir()
    for project in projects:
        project_dir = workspace_dir / "projects" / project["dir"]
        project_dir.mkdir()
        _create_project_config(
            project_dir, project["type"], project["name"], project["command"], project["description"]
        )


@pytest.fixture()
def cwd_with_workspace_sequential(tmp_path_factory: TempPathFactory) -> Path:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = [
        {
            "dir": "project1",
            "type": "contract",
            "name": "contract_project",
            "command": 'echo "hello contracts"',
            "description": "Prints hello",
        },
        {
            "dir": "project2",
            "type": "frontend",
            "name": "frontend_project",
            "command": 'echo "hello frontend"',
            "description": "Prints hello",
        },
    ]
    _create_workspace_project(cwd, projects)

    # Required for windows compatibility
    return cwd


@pytest.fixture()
def cwd_with_workspace(tmp_path_factory: TempPathFactory) -> Path:
    """
    Creates a standalone project with a single command.
    Single project is specified due to the fact that these are run concurrently,
    hence output stability is not guaranteed
    """

    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = [
        {
            "dir": "project1",
            "type": "contract",
            "name": "contract_project",
            "command": 'echo "hello contracts"',
            "description": "Prints hello",
        },
    ]
    _create_workspace_project(cwd, projects)

    # Required for windows compatibility
    return cwd


@pytest.fixture()
def cwd_with_standalone(tmp_path_factory: TempPathFactory) -> Path:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    cwd.mkdir()
    _create_project_config(cwd, "contract", "contract_project", 'echo "hello contracts"', "Prints hello contracts")

    # Required for windows compatibility
    return cwd


def test_run_command_from_workspace_success(cwd_with_workspace: Path) -> None:
    """
    Test running commands through the CLI.
    This includes both valid commands and handling of invalid commands.
    """
    result = invoke("project run hello", cwd=cwd_with_workspace)

    assert result.exit_code == 0
    verify(result.output)


def test_run_command_from_workspace_sequential_success(cwd_with_workspace_sequential: Path) -> None:
    """
    Test running commands through the CLI.
    This includes both valid commands and handling of invalid commands.
    """
    result = invoke("project run hello", cwd=cwd_with_workspace_sequential)

    assert result.exit_code == 0
    verify(result.output)


def test_run_command_from_standalone(cwd_with_standalone: Path) -> None:
    """
    Test running commands through the CLI.
    This includes both valid commands and handling of invalid commands.
    """
    result = invoke("project run hello", cwd=cwd_with_standalone)

    assert result.exit_code == 0
    verify(result.output)


def test_run_command_from_workspace_filtered(cwd_with_workspace_sequential: Path) -> None:
    """
    Test running commands through the CLI.
    This includes both valid commands and handling of invalid commands.
    """
    result = invoke("project run hello --project_name 'contract_project'", cwd=cwd_with_workspace_sequential)

    assert result.exit_code == 0
    verify(result.output)


def test_list_all_commands_in_workspace(cwd_with_workspace_sequential: Path) -> None:
    """
    Test running commands through the CLI.
    This includes both valid commands and handling of invalid commands.
    """
    result = invoke("project run hello --list", cwd=cwd_with_workspace_sequential)

    assert result.exit_code == 0
    verify(result.output)


def test_run_command_from_workspace_filtered_no_project(cwd_with_workspace_sequential: Path) -> None:
    """
    Test running commands through the CLI.
    This includes both valid commands and handling of invalid commands.
    """
    result = invoke("project run hello --project_name contract_project2", cwd=cwd_with_workspace_sequential)

    assert result.exit_code == 0
    verify(result.output)


def test_run_command_from_workspace_resolution_error(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = [
        {
            "dir": "project2",
            "type": "frontend",
            "name": "frontend_project",
            "command": "failthiscommand",
            "description": "Prints hello",
        },
    ]
    _create_workspace_project(cwd, projects)

    result = invoke("project run hello", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_run_command_from_workspace_execution_error(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = [
        {
            "dir": "project2",
            "type": "frontend",
            "name": "frontend_project",
            "command": 'python -c "raise Exception()"',
            "description": "Prints hello",
        },
    ]
    _create_workspace_project(cwd, projects)

    result = invoke("project run hello", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_run_command_from_standalone_resolution_error(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = [
        {
            "dir": "project2",
            "type": "frontend",
            "name": "frontend_project",
            "command": "failthiscommand",
            "description": "Prints hello",
        },
    ]
    _create_workspace_project(cwd, projects)

    result = invoke("project run hello", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_run_command_from_standalone_execution_error(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    cwd.mkdir()
    _create_project_config(
        cwd, "contract", "contract_project", 'python -c "raise Exception()"', "Prints hello contracts"
    )

    result = invoke("project run hello", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)
