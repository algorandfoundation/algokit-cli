"""Unit tests for package manager precedence hierarchy logic."""

from pathlib import Path
from unittest.mock import patch

from algokit.core.project.bootstrap import (
    _determine_javascript_package_manager,
    _determine_python_package_manager,
)


def test_python_package_manager_precedence_hierarchy(tmp_path: Path) -> None:
    """Test that Python package manager selection follows correct precedence."""
    project_dir = tmp_path

    # Test 1: Project override takes precedence over everything
    with (
        patch("algokit.core.project.bootstrap._get_py_package_manager_override", return_value="uv"),
        patch("algokit.core.project.bootstrap.get_py_package_manager", return_value="poetry"),
    ):
        result = _determine_python_package_manager(project_dir)
        assert result == "uv"

    # Test 2: User preference takes precedence over smart defaults
    (project_dir / "poetry.toml").write_text("")  # Would suggest poetry
    with (
        patch("algokit.core.project.bootstrap._get_py_package_manager_override", return_value=None),
        patch("algokit.core.project.bootstrap.get_py_package_manager", return_value="uv"),
    ):
        result = _determine_python_package_manager(project_dir)
        assert result == "uv"

    # Test 3: Smart defaults when no user preference
    with (
        patch("algokit.core.project.bootstrap._get_py_package_manager_override", return_value=None),
        patch("algokit.core.project.bootstrap.get_py_package_manager", return_value=None),
    ):
        result = _determine_python_package_manager(project_dir)
        assert result == "poetry"  # Should detect poetry.toml


def test_javascript_package_manager_precedence_hierarchy(tmp_path: Path) -> None:
    """Test that JavaScript package manager selection follows correct precedence."""
    project_dir = tmp_path

    # Test 1: Project override takes precedence over everything
    with (
        patch("algokit.core.project.bootstrap._get_js_package_manager_override", return_value="npm"),
        patch("algokit.core.project.bootstrap.get_js_package_manager", return_value="pnpm"),
    ):
        result = _determine_javascript_package_manager(project_dir)
        assert result == "npm"

    # Test 2: User preference takes precedence over smart defaults
    (project_dir / "pnpm-lock.yaml").write_text("")  # Would suggest pnpm
    with (
        patch("algokit.core.project.bootstrap._get_js_package_manager_override", return_value=None),
        patch("algokit.core.project.bootstrap.get_js_package_manager", return_value="npm"),
    ):
        result = _determine_javascript_package_manager(project_dir)
        assert result == "npm"

    # Test 3: Smart defaults when no user preference
    with (
        patch("algokit.core.project.bootstrap._get_js_package_manager_override", return_value=None),
        patch("algokit.core.project.bootstrap.get_js_package_manager", return_value=None),
    ):
        result = _determine_javascript_package_manager(project_dir)
        assert result == "pnpm"  # Should detect pnpm-lock.yaml


def test_interactive_prompt_saves_preference(tmp_path: Path) -> None:
    """Test that interactive prompt saves the user's choice."""
    project_dir = tmp_path

    with (
        patch("algokit.core.project.bootstrap._get_py_package_manager_override", return_value=None),
        patch("algokit.core.project.bootstrap.get_py_package_manager", return_value=None),
        patch("questionary.select") as mock_select,
        patch("algokit.core.project.bootstrap.save_py_package_manager") as mock_save,
    ):
        mock_select.return_value.ask.return_value = "uv"

        result = _determine_python_package_manager(project_dir)

        assert result == "uv"
        mock_save.assert_called_once_with("uv")
