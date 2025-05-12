import shutil
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from _pytest.tmpdir import TempPathFactory
from pytest_mock import MockerFixture

from algokit.core.typed_client_generation import AppSpecsNotFoundError
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock
from tests.utils.which_mock import WhichMock


@pytest.fixture
def which_mock(mocker: MockerFixture) -> WhichMock:
    """
    Fixture to mock 'shutil.which' with predefined responses.
    """
    which_mock = WhichMock()
    which_mock.add("npx")
    mocker.patch("algokit.core.utils.shutil.which").side_effect = which_mock.which
    return which_mock


@pytest.fixture(autouse=True)
def client_generator_mock(mocker: MockerFixture) -> MagicMock:
    """
    Fixture to mock 'shutil.which' with predefined responses.
    """

    client_gen_mock = MagicMock()
    mocker.patch("src.algokit.cli.generate.ClientGenerator.create_for_language", return_value=client_gen_mock)
    client_gen_mock.generate_all.return_value = None
    return client_gen_mock


def _format_output(output: str, replacements: list[tuple[str, str]]) -> str:
    """
    Modifies the output by replacing specified strings based on provided replacements.
    Each replacement is a tuple where the first element is the target string to find,
    and the second element is the string to replace it with. This function also ensures
    that lines starting with "DEBUG" are fully removed from the output.
    """
    for old, new in replacements:
        output = output.replace(old, new)
    output = output.replace("\\", "/")
    return "\n".join([line for line in output.split("\n") if not line.startswith("DEBUG")])


def _create_project_config(
    project_dir: Path,
    project_type: str,
    project_name: str,
    command: str,
    description: str,
    with_app_spec: bool = False,  # noqa: FBT001, FBT002
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
        if with_app_spec:
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
    with_app_spec: bool = True,
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
            project_dir,
            project["type"],
            project["name"],
            project["command"],
            project["description"],
            with_app_spec=with_app_spec,
        )


def _cwd_with_workspace(
    tmp_path_factory: TempPathFactory,
    which_mock: WhichMock,
    proc_mock: ProcMock,
    num_projects: int = 1,
    with_app_spec: bool = True,  # noqa: FBT002, FBT001
) -> Path:
    """
    Generates a workspace with specified number of projects.
    """

    def _generate_projects(num: int) -> list[dict[str, str]]:
        return [
            {
                "dir": f"project{i + 1}",
                "type": "frontend" if i == 0 else "contract",
                "name": f"contract_project_{i + 1}",
                "command": f"command_{chr(97 + i)}",
                "description": "Prints hello",
            }
            for i in range(num)
        ]

    cwd = tmp_path_factory.mktemp("cwd") / "algokit_project"
    projects = _generate_projects(num_projects)
    _create_workspace_project(
        workspace_dir=cwd,
        projects=projects,
        mock_command=True,
        which_mock=which_mock,
        proc_mock=proc_mock,
        with_app_spec=with_app_spec,
    )

    return cwd


def test_link_command_by_name_success(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock, client_generator_mock: MagicMock
) -> None:
    """
    Verifies 'project link' command success for a specific project name.
    """
    cwd_with_workspace = _cwd_with_workspace(tmp_path_factory, which_mock, proc_mock, num_projects=5)
    result = invoke("project link --project-name contract_project_3", cwd=cwd_with_workspace / "projects" / "project1")

    assert result.exit_code == 0
    client_generator_mock.generate_all.assert_called_once()
    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_all_success(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock, client_generator_mock: MagicMock
) -> None:
    """
    Confirms 'project link' command links all projects successfully.
    """
    contract_projects_count = 4
    frontend_projects_count = 1
    cwd_with_workspace = _cwd_with_workspace(
        tmp_path_factory, which_mock, proc_mock, num_projects=contract_projects_count + frontend_projects_count
    )
    result = invoke("project link --all", cwd=cwd_with_workspace / "projects" / "project1")

    assert result.exit_code == 0
    assert client_generator_mock.generate_all.call_count == contract_projects_count

    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_multiple_names_success(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock, client_generator_mock: MagicMock
) -> None:
    """
    Ensures 'project link' command success for multiple specified project names.
    """
    projects_count = 5
    cwd_with_workspace = _cwd_with_workspace(tmp_path_factory, which_mock, proc_mock, num_projects=projects_count)
    result = invoke(
        "project link --project-name contract_project_3 --project-name contract_project_5",
        cwd=cwd_with_workspace / "projects" / "project1",
    )

    assert result.exit_code == 0

    expected_call_count = 2
    assert client_generator_mock.generate_all.call_count == expected_call_count
    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_multiple_names_no_specs_success(
    tmp_path_factory: TempPathFactory, which_mock: WhichMock, proc_mock: ProcMock, client_generator_mock: MagicMock
) -> None:
    """
    Ensures 'project link' command success for multiple specified project names.
    """
    cwd_with_workspace = _cwd_with_workspace(
        tmp_path_factory, which_mock, proc_mock, num_projects=5, with_app_spec=False
    )
    client_generator_mock.generate_all.side_effect = Mock(side_effect=AppSpecsNotFoundError())

    result = invoke(
        "project link --project-name contract_project_3 --project-name contract_project_5",
        cwd=cwd_with_workspace / "projects" / "project1",
    )

    assert result.exit_code == 0
    assert client_generator_mock.generate_all.call_count == 2  # noqa: PLR2004

    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_name_not_found(
    tmp_path_factory: TempPathFactory,
    which_mock: WhichMock,
    proc_mock: ProcMock,
) -> None:
    """
    Ensures 'project link' command success for project that does not exist.
    """
    cwd_with_workspace = _cwd_with_workspace(tmp_path_factory, which_mock, proc_mock, num_projects=5)
    result = invoke(
        "project link --project-name contract_project_13",
        cwd=cwd_with_workspace / "projects" / "project1",
    )

    assert result.exit_code == 0
    verify(_format_output(result.output, [(str(cwd_with_workspace), "<cwd>")]))


def test_link_command_empty_folder(
    tmp_path_factory: TempPathFactory,
) -> None:
    """
    Ensures 'project link' command success for empty folder.
    """
    cwd = tmp_path_factory.mktemp("cwd")
    result = invoke("project link --all", cwd=cwd)

    assert result.exit_code == 0
    verify(_format_output(result.output, [(str(cwd), "<cwd>")]))
