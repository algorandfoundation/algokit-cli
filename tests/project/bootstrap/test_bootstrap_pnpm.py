"""Essential tests for pnpm bootstrap functionality.
Focuses on critical scenarios: success, failure, and CI mode validation.
"""

import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.pytest.py_test_namer import PyTestNamer

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.mark.usefixtures("mock_platform_system", "proc_mock")
def test_bootstrap_pnpm_happy_path(tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest) -> None:
    """Test successful pnpm bootstrap."""
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke("project bootstrap pnpm --no-ci", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))


def test_bootstrap_pnpm_without_package_file(tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest) -> None:
    """Test pnpm bootstrap when package.json doesn't exist."""
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke("project bootstrap pnpm --no-ci", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output, namer=PyTestNamer(request))


def test_bootstrap_pnpm_ci_mode_without_lock_file(
    tmp_path_factory: TempPathFactory, request: pytest.FixtureRequest
) -> None:
    """Test pnpm bootstrap in CI mode without lock file fails appropriately."""
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "package.json").touch()

    result = invoke("project bootstrap pnpm --ci", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output, namer=PyTestNamer(request))
