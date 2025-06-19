from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.pytest.py_test_namer import PyTestNamer

from algokit.core.conf import ALGOKIT_CONFIG, get_current_package_version
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def _setup_workspace(cwd: Path) -> None:
    """
    Sets up the workspace configuration.
    """
    algokit_config_path = cwd / ".algokit.toml"
    algokit_config_path.write_text(
        """
        [project]
        type = "workspace"
        projects_root_dir = 'artifacts'
        """
    )


def _setup_standalone_project(cwd: Path, project_name: str, project_type: str) -> None:
    """
    Sets up a standalone project of a specified type within the workspace.
    """
    project_dir = cwd / "artifacts" / project_name
    project_dir.mkdir(parents=True)
    project_config_path = project_dir / ".algokit.toml"
    project_config_path.write_text(
        f"""
        [project]
        type = "{project_type}"
        name = "{project_name}"
        """
    )
    (project_dir / ".env.template").touch()
    if project_type == "contract":
        (project_dir / "poetry.toml").touch()
    elif project_type == "frontend":
        (project_dir / "package.json").touch()


def test_bootstrap_all_empty(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "project bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_all_algokit_min_version(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    current_version = get_current_package_version()
    (cwd / ALGOKIT_CONFIG).write_text('[algokit]\nmin_version = "999.99.99"\n')
    result = invoke(
        "project bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output.replace(current_version, "{current_version}"))


def test_bootstrap_all_algokit_min_version_ignore_error(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    current_version = get_current_package_version()
    (cwd / ALGOKIT_CONFIG).write_text('[algokit]\nmin_version = "999.99.99"\n')
    result = invoke(
        "project bootstrap --force all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output.replace(current_version, "{current_version}"))


def test_bootstrap_all_env(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env.template").touch()

    result = invoke(
        "project bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_poetry(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "poetry.toml").touch()

    result = invoke(
        "project bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("mock_platform_system", "proc_mock")
def test_bootstrap_all_npm(tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke(
        "project bootstrap all --interactive",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_poetry_via_pyproject(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "pyproject.toml").write_text("[tool.poetry]", encoding="utf-8")

    result = invoke(
        "project bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_all_skip_dirs(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".venv").mkdir()
    (cwd / "__pycache__").mkdir()
    (cwd / "node_modules").mkdir()
    (cwd / "file.txt").touch()
    (cwd / "empty_dir").mkdir()
    (cwd / "boring_dir").mkdir()
    (cwd / "boring_dir" / "file.txt").touch()
    (cwd / "double_nested_dir").mkdir()
    (cwd / "double_nested_dir" / "nest1").mkdir()
    (cwd / "double_nested_dir" / "nest2").mkdir()
    (cwd / "double_nested_dir" / "nest2" / "file.txt").touch()

    result = invoke(
        "project bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_sub_dir(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "empty_dir").mkdir()
    (cwd / "live_dir").mkdir()
    (cwd / "live_dir" / ".env.template").touch()
    (cwd / "live_dir" / "poetry.toml").touch()

    result = invoke(
        "project bootstrap all",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_projects_name_filter(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    _setup_workspace(cwd)
    _setup_standalone_project(cwd, "project_1", "contract")
    result = invoke("project bootstrap all --project-name project_1", cwd=cwd)
    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_projects_name_filter_not_found(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    _setup_workspace(cwd)
    _setup_standalone_project(cwd, "project_1", "contract")
    result = invoke("project bootstrap all --project-name project_2", cwd=cwd)
    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_projects_type_filter(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    _setup_workspace(cwd)
    _setup_standalone_project(cwd, "project_1", "contract")
    _setup_standalone_project(cwd, "project_2", "contract")
    _setup_standalone_project(cwd, "project_3", "contract")
    _setup_standalone_project(cwd, "project_4", "frontend")

    result = invoke("project bootstrap all --type frontend --interactive", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output.replace(".cmd", ""))


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_all_projects_type_filter_not_found(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    _setup_workspace(cwd)
    _setup_standalone_project(cwd, "project_1", "contract")
    _setup_standalone_project(cwd, "project_2", "contract")
    _setup_standalone_project(cwd, "project_3", "contract")

    result = invoke("project bootstrap all --type frontend", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)
