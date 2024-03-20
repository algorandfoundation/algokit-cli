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
    which_mock = WhichMock()
    mocker.patch("algokit.core.utils.shutil.which").side_effect = which_mock.which
    return which_mock


def _format_output(output: str, replacements: list[tuple[str, str]], remove_debug: bool = True) -> str:  # noqa: FBT002, FBT001
    """
    Modifies the output by replacing specified strings based on provided replacements.
    Each replacement is a tuple where the first element is the target string to find,
    and the second element is the string to replace it with. This function also ensures
    that lines starting with "DEBUG" are fully removed from the output.
    """
    for old, new in replacements:
        output = output.replace(old, new)
    return "\n".join([line for line in output.split("\n") if not (remove_debug and line.startswith("DEBUG"))]).replace(
        "\\", r"\\"
    )


def _create_project_config(
    project_dir: Path, project_type: str, project_name: str, command: str, description: str
) -> None:
    """
    Creates a .algokit.toml configuration file in the specified project directory.

    Args:
        project_dir (Path): The directory of the project.
        project_type (str): The type of the project.
        project_name (str): The name of the project.
        command (str): The command associated with the project.
        description (str): A description of the project.
    """
    project_config = f"""
[project]
type = '{project_type}'
name = '{project_name}'

[project.run]
hello = {{ commands = ['{command}'], description = '{description}' }}
    """.strip()
    (project_dir / ".algokit.toml").write_text(project_config, encoding="utf-8")


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
    Creates a workspace project and its subprojects within the specified directory.

    Args:
        workspace_dir (Path): The directory of the workspace.
        projects (list[dict[str, str]]): A list of dictionaries, each representing a project with
        keys for directory, type, name, command, and description.
        mock_command (bool, optional): Indicates whether to mock the command. Defaults to False.
        which_mock (WhichMock | None, optional): The mock object for the 'which' command. Defaults to None.
        proc_mock (ProcMock | None, optional): The mock object for the process execution. Defaults to None.
        custom_project_order (list[str] | None, optional): Specifies a custom order for project execution.
        Defaults to None.
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
    Creates a workspace with a specified number of standalone projects, each with a single command.
    Projects are generated in a loop based on the number specified.
    """

    def _generate_projects(num: int) -> list[dict[str, str]]:
        return [
            {
                "dir": f"project{i+1}",
                "type": "contract",
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


def test_list_command_from_workspace_success(
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
    cwd_with_workspace = _cwd_with_workspace(tmp_path_factory, which_mock, proc_mock, num_projects=20)
    result = invoke(f"project list {cwd_with_workspace}".split(), cwd=cwd_with_workspace)

    assert result.exit_code == 0
    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_list_command_from_empty_folder(
    tmp_path_factory: TempPathFactory,
) -> None:
    """
    Test to verify that the 'project list' command executes successfully in an empty directory.

    This test ensures that executing the command in a directory without any projects or workspace
      configuration does not result in errors.

    Args:
        tmp_path_factory (TempPathFactory): A fixture to create temporary directories.
    """
    empty_cwd = tmp_path_factory.mktemp("cwd")
    result = invoke(f"project list {empty_cwd}".split(), cwd=empty_cwd)

    assert result.exit_code == 0
    verify(
        _format_output(
            result.output,
            [(str(empty_cwd.parent), "<cwd>"), (str(empty_cwd.parent.parent), "<cwd>")],
            remove_debug=False,
        )
    )


def test_list_command_no_args(
    tmp_path_factory: TempPathFactory,
) -> None:
    """
    Test to ensure the 'project list' command executes successfully without specifying a directory.

    This test checks that the command can be executed in an empty directory without passing any
    arguments, and it completes without errors.

    Args:
        tmp_path_factory (TempPathFactory): A fixture to create temporary directories.
    """
    empty_cwd = tmp_path_factory.mktemp("cwd")
    result = invoke("project list", cwd=empty_cwd)

    assert result.exit_code == 0
    verify(
        _format_output(
            result.output,
            [(str(empty_cwd.parent), "<cwd>"), (str(empty_cwd.parent.parent), "<cwd>")],
            remove_debug=False,
        )
    )
