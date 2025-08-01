"""Focused tests for package manager selection logic in bootstrap.
Tests only the new configuration-driven behavior, not redundant scenarios.
"""

import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.pytest.py_test_namer import PyTestNamer
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_respects_configured_package_managers(
    tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest, mocker: MockerFixture
) -> None:
    """Test that bootstrap respects user's configured package managers."""
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "pyproject.toml").write_text('[project]\nname = "test"\nversion = "0.1.0"')
    (cwd / "package.json").touch()
    (cwd / "pnpm-lock.yaml").touch()  # Required for CI mode

    # Mock user preferences
    mocker.patch("algokit.core.project.bootstrap.get_py_package_manager", return_value="uv")
    mocker.patch("algokit.core.project.bootstrap.get_js_package_manager", return_value="pnpm")

    result = invoke("project bootstrap all", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))
