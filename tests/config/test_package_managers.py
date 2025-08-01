"""
Essential tests for package manager configuration commands.
Focuses on critical user-facing functionality only.
"""

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke

# Exit codes
INVALID_ARGUMENT_EXIT_CODE = 2


def test_js_package_manager_help() -> None:
    """Test help output for js-package-manager command."""
    result = invoke("config js-package-manager --help")
    assert result.exit_code == 0
    verify(result.output)


def test_py_package_manager_help() -> None:
    """Test help output for py-package-manager command."""
    result = invoke("config py-package-manager --help")
    assert result.exit_code == 0
    verify(result.output)


def test_js_package_manager_invalid_argument() -> None:
    """Test error handling for invalid js package manager."""
    result = invoke("config js-package-manager invalid")
    assert result.exit_code == INVALID_ARGUMENT_EXIT_CODE
    verify(result.output)


def test_py_package_manager_invalid_argument() -> None:
    """Test error handling for invalid py package manager."""
    result = invoke("config py-package-manager invalid")
    assert result.exit_code == INVALID_ARGUMENT_EXIT_CODE
    verify(result.output)


def test_js_package_manager_set_npm() -> None:
    """Test setting npm as js package manager."""
    result = invoke("config js-package-manager npm")
    assert result.exit_code == 0
    verify(result.output)


def test_js_package_manager_set_pnpm() -> None:
    """Test setting pnpm as js package manager."""
    result = invoke("config js-package-manager pnpm")
    assert result.exit_code == 0
    verify(result.output)


def test_py_package_manager_set_poetry() -> None:
    """Test setting poetry as py package manager."""
    result = invoke("config py-package-manager poetry")
    assert result.exit_code == 0
    verify(result.output)


def test_py_package_manager_set_uv() -> None:
    """Test setting uv as py package manager."""
    result = invoke("config py-package-manager uv")
    assert result.exit_code == 0
    verify(result.output)
