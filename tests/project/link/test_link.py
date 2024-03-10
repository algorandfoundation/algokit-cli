import shutil
from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock
from tests.utils.which_mock import WhichMock


@pytest.fixture()
def which_mock(mocker: MockerFixture) -> WhichMock:
    """
    Fixture to mock 'shutil.which' with predefined responses.
    """
    which_mock = WhichMock()
    which_mock.add("npx")
    mocker.patch("algokit.core.utils.shutil.which").side_effect = which_mock.which
    return which_mock


def _format_output(output: str, replacements: list[tuple[str, str]]) -> str:
    """
    Modifies the output by replacing specified strings based on provided replacements.
    Each replacement is a tuple where the first element is the target string to find,
    and the second element is the string to replace it with. This function also ensures
    that lines starting with "DEBUG" are fully removed from the output.
    """
    for old, new in replacements:
        output = output.replace(old, new)
    return "\n".join([line for line in output.split("\n") if not line.startswith("DEBUG")])


def _create_project_config(
    project_dir: Path, project_type: str, project_name: str, command: str, description: str
) -> None:
    """
    Generates .algokit.toml configuration file in project directory.
    """
    project_config = f"""
[project]
type = '{project_type}'
name = '{project_name}'
artifacts = 'dist'

[project.run]
hello = {{ commands = ['{command}'], description = '{description}' }}
    """.strip()
    (project_dir / ".algokit.toml").write_text(project_config, encoding="utf-8")

    if project_type == "contract":
        (project_dir / "dist").mkdir()
        app_spec_example_path = Path(__file__).parent / "application.json"
        shutil.copy(app_spec_example_path, project_dir / "dist" / "application.json")


def _create_workspace_project(
    *,
    workspace_dir: Path,
    projects: list[dict[str, str]],
    mock_command: bool = False,
    which_mock: WhichMock | None = None,
    proc_mock: ProcMock | None = None,
    custom_project_order: list[str] | None = None,
) -> None:
    """
    Sets up a workspace and its subprojects.
    """
    workspace_dir.mkdir()
    custom_project_order = custom_project_order if custom_project_order else ["contract_project", "frontend_project"]
    (workspace_dir / ".algokit.toml").write_text(
        f"""
[project]
type = 'workspace'
projects_root_path = 'projects'

[project.run]
hello = {custom_project_order}
        """.strip(),
        encoding="utf-8",
    )
    (workspace_dir / "projects").mkdir()
    for project in projects:
        project_dir = workspace_dir / "projects" / project["dir"]
        project_dir.mkdir()
        if mock_command and proc_mock and which_mock:
            resolved_mocked_cmd = which_mock.add(project["command"])
            proc_mock.set_output([resolved_mocked_cmd], ["picked " + project["command"]])

        _create_project_config(
            project_dir, project["type"], project["name"], project["command"], project["description"]
        )


def _cwd_with_workspace(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock, num_projects: int = 1
) -> Path:
    """
    Generates a workspace with specified number of projects.
    """

    def _generate_projects(num: int) -> list[dict[str, str]]:
        return [
            {
                "dir": f"project{i+1}",
                "type": "frontend" if i == 0 else "contract",
                "name": f"contract_project_{i+1}",
                "command": f"command_{chr(97+i)}",
                "description": "Prints hello",
            }
            for i in range(num)
        ]

    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = _generate_projects(num_projects)
    _create_workspace_project(
        workspace_dir=cwd, projects=projects, mock_command=True, which_mock=which_mock, proc_mock=proc_mock
    )

    return cwd


def test_link_command_by_name_success(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock
) -> None:
    """
    Verifies 'project list' command success for a specific project name.
    """
    cwd_with_workspace = _cwd_with_workspace(tmp_path_factory, which_mock, proc_mock, num_projects=5)
    result = invoke("project link --project-name contract_project_3", cwd=cwd_with_workspace / "projects" / "project1")

    assert result.exit_code == 0
    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_all_success(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock
) -> None:
    """
    Confirms 'project list' command lists all projects successfully.
    """
    cwd_with_workspace = _cwd_with_workspace(tmp_path_factory, which_mock, proc_mock, num_projects=5)
    result = invoke("project link --all", cwd=cwd_with_workspace / "projects" / "project1")

    assert result.exit_code == 0
    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_multiple_names_success(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock
) -> None:
    """
    Ensures 'project list' command success for multiple specified project names.
    """
    cwd_with_workspace = _cwd_with_workspace(tmp_path_factory, which_mock, proc_mock, num_projects=5)
    result = invoke(
        "project link --project-name contract_project_3 --project-name contract_project_5",
        cwd=cwd_with_workspace / "projects" / "project1",
    )

    assert result.exit_code == 0
    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_name_not_found(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock
) -> None:
    """
    Test to ensure the 'project list' command executes successfully within a workspace containing multiple projects.

    This test simulates a workspace environment with 20 projects and verifies that the
    command lists all projects without errors.

    Args:
        tmp_path_factory (TempPathFactory): A fixture to create temporary directories.
        which_mock (WhichMock): A mock for the 'which' command.
        proc_mock (ProcMock): A mock for process execution.
    """
    cwd_with_workspace = _cwd_with_workspace(tmp_path_factory, which_mock, proc_mock, num_projects=5)
    result = invoke(
        "project link --project-name contract_project_13",
        cwd=cwd_with_workspace / "projects" / "project1",
    )

    assert result.exit_code == 1
    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_empty_folder(
    tmp_path_factory: TempPathFactory,
) -> None:
    """
    Test to ensure the 'project list' command executes successfully within a workspace containing multiple projects.

    This test simulates a workspace environment with 20 projects and verifies that the
    command lists all projects without errors.

    Args:
        tmp_path_factory (TempPathFactory): A fixture to create temporary directories.
        which_mock (WhichMock): A mock for the 'which' command.
        proc_mock (ProcMock): A mock for process execution.
    """
    cwd = tmp_path_factory.mktemp("cwd")
    result = invoke("project link --all", cwd=cwd)

    assert result.exit_code == 0
    verify(_format_output(result.output, [(str(cwd), "<cwd>")]))
