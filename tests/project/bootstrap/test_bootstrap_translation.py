"""Tests for package manager command translation during bootstrap."""

import tempfile
from pathlib import Path

import pytest

from algokit.core.project.bootstrap import (
    _translate_package_manager_in_toml,
    _translate_single_command,
)


@pytest.mark.parametrize(
    ("cmd", "js_manager", "py_manager", "expected"),
    [
        # JavaScript translations - compatible commands
        ("npm run build", "pnpm", None, "pnpm run build"),
        ("npm install", "pnpm", None, "pnpm install"),
        ("npm test", "pnpm", None, "pnpm test"),
        ("npm start", "pnpm", None, "pnpm start"),
        ("pnpm run build", "npm", None, "npm run build"),
        ("pnpm install", "npm", None, "npm install"),
        ("pnpm test", "npm", None, "npm test"),
        ("pnpm start", "npm", None, "npm start"),
        # JavaScript incompatible commands (no translation)
        ("npm exec jest", "pnpm", None, "npm exec jest"),  # Different behavior
        ("npx create-react-app", "pnpm", None, "npx create-react-app"),  # Different behavior
        ("npm fund", "pnpm", None, "npm fund"),  # No pnpm equivalent
        ("pnpm exec jest", "npm", None, "pnpm exec jest"),  # Different behavior
        ("pnpm dlx create-react-app", "npm", None, "pnpm dlx create-react-app"),  # No npm equivalent
        # Python translations - compatible commands
        ("poetry install", None, "uv", "uv sync"),
        ("poetry install --verbose", None, "uv", "uv sync --verbose"),
        ("poetry run pytest", None, "uv", "uv run pytest"),
        ("poetry add requests", None, "uv", "uv add requests"),
        ("poetry remove django", None, "uv", "uv remove django"),
        ("poetry lock", None, "uv", "uv lock"),
        ("uv sync", None, "poetry", "poetry install"),
        ("uv run python app.py", None, "poetry", "poetry run python app.py"),
        ("uv add numpy", None, "poetry", "poetry add numpy"),
        # Python incompatible commands (no translation)
        ("poetry show", None, "uv", "poetry show"),  # No equivalent
        ("poetry config", None, "uv", "poetry config"),  # No equivalent
        ("uv pip install", None, "poetry", "uv pip install"),  # No equivalent
        # No translation cases
        ("npm run build", None, None, "npm run build"),
        ("echo hello", "pnpm", "uv", "echo hello"),
    ],
)
def test_translate_single_command(cmd: str, js_manager: str | None, py_manager: str | None, expected: str) -> None:
    """Test command translation logic."""
    assert _translate_single_command(cmd, js_manager, py_manager) == expected


def test_translate_toml_file() -> None:
    """Test that .algokit.toml file is correctly translated."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir)
        toml_path = project_dir / ".algokit.toml"

        # Create initial .algokit.toml
        toml_content = """
[project.run]
build = { commands = ["npm run build", "poetry run test"] }
"""
        toml_path.write_text(toml_content)

        # Translate
        _translate_package_manager_in_toml(project_dir, "pnpm", "uv")

        # Verify by checking the file content
        result_content = toml_path.read_text()
        assert '"pnpm run build"' in result_content
        assert '"uv run test"' in result_content
        assert '"npm run build"' not in result_content
        assert '"poetry run test"' not in result_content


def test_translate_preserves_non_command_content() -> None:
    """Test that translation preserves other TOML content."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir)
        toml_path = project_dir / ".algokit.toml"

        # Create .algokit.toml with various content
        original = """
[algokit]
min_version = "1.0.0"

[project]
name = "test"
type = "backend"

[project.run]
dev = { commands = ["npm start"], description = "Start dev" }
"""
        toml_path.write_text(original)

        # Translate
        _translate_package_manager_in_toml(project_dir, "pnpm", None)

        # Verify structure is preserved
        result_content = toml_path.read_text()
        # Check that non-command content is preserved
        assert 'min_version = "1.0.0"' in result_content
        assert 'name = "test"' in result_content
        assert 'type = "backend"' in result_content
        assert 'description = "Start dev"' in result_content
        # Check that command was translated
        assert '"pnpm start"' in result_content
        assert '"npm start"' not in result_content
