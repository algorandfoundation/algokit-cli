import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock
from tests.utils.which_mock import WhichMock

DirWithAppSpecFactory = Callable[[Path], Path]

PYTHON_EXECUTABLE = sys.executable
# need to use an escaped python executable path in config files for windows
PYTHON_EXECUTABLE_ESCAPED = PYTHON_EXECUTABLE.replace("\\", "\\\\")


def _strip_line_starting_with(output: str, start_str: str) -> str:
    return "\n".join([line for line in output.split("\n") if not line.startswith(start_str)])


@pytest.fixture()
def which_mock(mocker: MockerFixture) -> WhichMock:
    which_mock = WhichMock()
    mocker.patch("algokit.core.utils.shutil.which").side_effect = which_mock.which
    return which_mock


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
    Creates a workspace project and its subprojects.
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


@pytest.fixture()
def cwd_with_workspace_sequential(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock
) -> Path:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = [
        {
            "dir": "project1",
            "type": "contract",
            "name": "contract_project",
            "command": "command_a",
            "description": "Prints hello",
        },
        {
            "dir": "project2",
            "type": "frontend",
            "name": "frontend_project",
            "command": "command_b",
            "description": "Prints hello",
        },
    ]
    _create_workspace_project(
        workspace_dir=cwd, projects=projects, mock_command=True, which_mock=which_mock, proc_mock=proc_mock
    )

    # Required for windows compatibility
    return cwd


@pytest.fixture()
def cwd_with_workspace(tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock) -> Path:
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
            "command": "command_a",
            "description": "Prints hello",
        },
    ]
    _create_workspace_project(
        workspace_dir=cwd, projects=projects, mock_command=True, which_mock=which_mock, proc_mock=proc_mock
    )

    # Required for windows compatibility
    return cwd


@pytest.fixture()
def cwd_with_standalone(tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock) -> Path:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    cwd.mkdir()

    which_mock.add("command_a")
    proc_mock.set_output(["command_a"], ["picked command_a"])
    _create_project_config(cwd, "contract", "contract_project", "command_a", "Prints hello contracts")

    # Required for windows compatibility
    return cwd


def test_run_command_from_workspace_success(
    cwd_with_workspace: Path,
) -> None:
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


def test_run_command_from_workspace_resolution_error(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
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
    _create_workspace_project(
        workspace_dir=cwd,
        projects=projects,
    )

    result = invoke("project run hello", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_run_command_from_workspace_execution_error(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = [
        {
            "dir": "project2",
            "type": "frontend",
            "name": "frontend_project",
            "command": PYTHON_EXECUTABLE_ESCAPED + ' -c "raise Exception()"',
            "description": "Prints hello",
        },
    ]
    _create_workspace_project(
        workspace_dir=cwd,
        projects=projects,
    )

    result = invoke("project run hello", cwd=cwd)

    assert result.exit_code == 1
    verify(_strip_line_starting_with(result.output, "DEBUG"))


def test_run_command_from_standalone_resolution_error(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
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
    _create_workspace_project(
        workspace_dir=cwd,
        projects=projects,
    )

    result = invoke("project run hello", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_run_command_from_standalone_execution_error(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    cwd.mkdir()
    _create_project_config(
        cwd,
        "contract",
        "contract_project",
        PYTHON_EXECUTABLE_ESCAPED + ' -c "raise Exception()"',
        "Prints hello contracts",
    )

    result = invoke("project run hello", cwd=cwd)

    assert result.exit_code == 1
    verify(_strip_line_starting_with(result.output, "DEBUG"))


def test_run_command_from_workspace_partially_sequential(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock
) -> None:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = []
    for i in range(1, 6):
        projects.append(
            {
                "dir": f"project{i}",
                "type": "contract",
                "name": f"contract_project_{i}",
                "command": f"hello{i}",
                "description": "Prints hello",
            }
        )
    _create_workspace_project(
        workspace_dir=cwd,
        projects=projects,
        mock_command=True,
        which_mock=which_mock,
        proc_mock=proc_mock,
        custom_project_order=["contract_project_1", "contract_project_4"],
    )

    result = invoke("project run hello", cwd=cwd)
    assert result.exit_code == 0
    verify(_strip_line_starting_with(result.output, "✅"))
