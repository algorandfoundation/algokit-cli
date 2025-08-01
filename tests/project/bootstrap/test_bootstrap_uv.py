"""Essential tests for uv bootstrap functionality.
Focuses on key scenarios: happy path, missing uv, and poetry migration.
"""

import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.pytest.py_test_namer import PyTestNamer
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_uv_happy_path(tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest) -> None:
    """Test successful uv bootstrap when uv is installed."""
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "pyproject.toml").write_text('[project]\nname = "test"\nversion = "0.1.0"')

    result = invoke("project bootstrap uv", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))


def test_bootstrap_uv_user_declines_install(
    proc_mock: ProcMock, tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest, mocker: MockerFixture
) -> None:
    """Test uv bootstrap when uv is not installed and user declines installation."""
    proc_mock.should_fail_on("uv --version")
    mocker.patch("algokit.core.questionary_extensions.prompt_confirm", return_value=False)

    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "pyproject.toml").write_text('[project]\nname = "test"\nversion = "0.1.0"')

    result = invoke("project bootstrap uv", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output, namer=PyTestNamer(request))


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_uv_poetry_project_migration_declined(
    tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest, mocker: MockerFixture
) -> None:
    """Test uv bootstrap with poetry project when user declines migration."""
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "pyproject.toml").write_text('[tool.poetry]\nname = "test"\nversion = "0.1.0"')

    mocker.patch("algokit.core.questionary_extensions.prompt_confirm", return_value=False)

    result = invoke("project bootstrap uv", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output, namer=PyTestNamer(request))
