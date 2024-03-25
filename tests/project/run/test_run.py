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
# Escaping the python executable path for use in config files on Windows platforms
PYTHON_EXECUTABLE_ESCAPED = PYTHON_EXECUTABLE.replace("\\", "\\\\")


def _format_output(output: str) -> str:
    """
    Strips lines from the output that start with the specified string.

    Args:
        output (str): The output string to process.
        start_str (str): The string that identifies the start of lines to be stripped.

    Returns:
        str: The processed output with specified lines stripped.
    """
    output = "\n".join([line for line in output.split("\n") if not line.startswith("DEBUG")])
    return output.replace(PYTHON_EXECUTABLE_ESCAPED, "<sys.executable>").replace("\\", r"\\")


@pytest.fixture(autouse=True)
def _disable_animation(mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.utils.animate", return_value=None)


@pytest.fixture()
def which_mock(mocker: MockerFixture) -> WhichMock:
    which_mock = WhichMock()
    mocker.patch("algokit.core.utils.shutil.which").side_effect = which_mock.which
    return which_mock


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

    return cwd


@pytest.fixture()
def cwd_with_standalone(tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock) -> Path:
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    cwd.mkdir()

    which_mock.add("command_a")
    proc_mock.set_output(["command_a"], ["picked command_a"])
    _create_project_config(cwd, "contract", "contract_project", "command_a", "Prints hello contracts")

    return cwd


def test_run_command_from_workspace_success(
    cwd_with_workspace: Path,
) -> None:
    """
    Verifies successful command execution within a workspace project.

    Args:
        cwd_with_workspace (Path): The path to the workspace directory.
    """
    result = invoke("project run hello", cwd=cwd_with_workspace)

    assert result.exit_code == 0
    verify(_format_output(result.output))


def test_run_command_from_workspace_sequential_success(cwd_with_workspace_sequential: Path) -> None:
    """
    Verifies successful sequential command execution within a workspace project.

    Args:
        cwd_with_workspace_sequential (Path): The path to the workspace directory.
    """
    result = invoke("project run hello", cwd=cwd_with_workspace_sequential)

    assert result.exit_code == 0
    verify(_format_output(result.output))


def test_run_command_from_standalone(cwd_with_standalone: Path) -> None:
    """
    Verifies successful command execution within a standalone project.

    Args:
        cwd_with_standalone (Path): The path to the standalone project directory.
    """
    result = invoke("project run hello", cwd=cwd_with_standalone)

    assert result.exit_code == 0
    verify(_format_output(result.output))


def test_run_command_from_workspace_filtered(cwd_with_workspace_sequential: Path) -> None:
    """
    Verifies successful command execution within a workspace project with filtering by project name.

    Args:
        cwd_with_workspace_sequential (Path): The path to the workspace directory.
    """
    result = invoke("project run hello --project-name 'contract_project'", cwd=cwd_with_workspace_sequential)

    assert result.exit_code == 0
    verify(_format_output(result.output))


def test_list_all_commands_in_workspace(cwd_with_workspace_sequential: Path) -> None:
    """
    Lists all commands available within a workspace project.

    Args:
        cwd_with_workspace_sequential (Path): The path to the workspace directory.
    """
    result = invoke("project run hello --list", cwd=cwd_with_workspace_sequential)

    assert result.exit_code == 0
    verify(_format_output(result.output))


def test_run_command_from_workspace_filtered_no_project(cwd_with_workspace_sequential: Path) -> None:
    """
    Verifies command execution within a workspace project when the specified project does not exist.

    Args:
        cwd_with_workspace_sequential (Path): The path to the workspace directory.
    """
    result = invoke("project run hello --project-name contract_project2", cwd=cwd_with_workspace_sequential)

    assert result.exit_code == 0
    verify(_format_output(result.output))


def test_run_command_from_workspace_resolution_error(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """
    Verifies the behavior when a command resolution error occurs within a workspace project.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Pytest fixture to create temporary directories.
    """

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
    verify(_format_output(result.output))


def test_run_command_from_workspace_execution_error(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """
    Verifies the behavior when a command execution error occurs within a workspace project.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Pytest fixture to create temporary directories.
    """
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
    verify(_format_output(result.output))


def test_run_command_from_standalone_resolution_error(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """
    Verifies the behavior when a command resolution error occurs within a standalone project.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Pytest fixture to create temporary directories.
    """
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

    result = invoke("project run hello", cwd=cwd / "projects" / "project2")

    assert result.exit_code == 1
    verify(_format_output(result.output))


def test_run_command_from_standalone_execution_error(tmp_path_factory: pytest.TempPathFactory) -> None:
    """
    Verifies the behavior when a command execution error occurs within a standalone project.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Pytest fixture to create temporary directories.
    """
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
    verify(_format_output(result.output))


def test_run_command_from_workspace_partially_sequential(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock
) -> None:
    """
    Verifies successful execution of commands in a partially sequential order within a workspace project.

    Args:
        tmp_path_factory (TempPathFactory): Pytest fixture to create temporary directories.
        which_mock (WhichMock): Mock object for the 'which' command.
        proc_mock (ProcMock): Mock object for process execution.
    """
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
    order_of_execution = [line for line in result.output.split("\n") if line.startswith("✅")]
    assert "contract_project_1" in order_of_execution[0]
    assert "contract_project_4" in order_of_execution[1]


def test_run_command_from_standalone_pass_env(
    tmp_path_factory: TempPathFactory,
) -> None:
    """
    Verifies successful command execution within a standalone project with environment variables passed.

    Args:
        tmp_path_factory (TempPathFactory): Pytest fixture to create temporary directories.
    """
    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    cwd.mkdir()
    (cwd / "print_env.py").write_text('import os; print(os.environ.get("HELLO"))')

    _create_project_config(
        cwd,
        "contract",
        "contract_project",
        PYTHON_EXECUTABLE_ESCAPED + " print_env.py",
        "Prints hello contracts",
    )
    result = invoke("project run hello", cwd=cwd, env={"HELLO": "Hello World from env variable!"})

    assert result.exit_code == 0
    verify(_format_output(result.output))


def test_run_command_help_works_without_path_resolution(
    tmp_path_factory: TempPathFactory,
    which_mock: WhichMock,
    proc_mock: ProcMock,
) -> None:
    """
    Verifies that the help command works without path resolution.
    """

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
        mock_command=False,
        which_mock=which_mock,
        proc_mock=proc_mock,
        custom_project_order=["contract_project_1", "contract_project_4"],
    )

    result = invoke("project run --help", cwd=cwd)

    assert result.exit_code == 0
    verify(_format_output(result.output))

    assert invoke("project run hello", cwd=cwd).exit_code == 1
