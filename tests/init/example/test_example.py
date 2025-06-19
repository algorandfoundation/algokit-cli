import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.which_mock import WhichMock

MOCK_EXAMPLES = [
    {"id": "react-vite", "name": "React Vite", "type": "frontend"},
    {"id": "python-smart-contract", "name": "Python Smart Contract", "type": "contract"},
]
# Define constants relative to the mocked Path.home() which will be tmp_path
MOCK_USER_DIR_NAME = ".algokit"
MOCK_TEMPLATES_DIR_NAME = "templates"
MOCK_EXAMPLES_DIR_NAME = "examples"
MOCK_EXAMPLES_CONFIG_NAME = "examples.yml"


def get_mock_user_dir(home_path: Path) -> Path:
    return home_path / MOCK_USER_DIR_NAME


def get_mock_templates_dir(home_path: Path) -> Path:
    return get_mock_user_dir(home_path) / MOCK_TEMPLATES_DIR_NAME


def get_mock_examples_dir(home_path: Path) -> Path:
    return get_mock_templates_dir(home_path) / MOCK_EXAMPLES_DIR_NAME


def get_mock_examples_config_path(home_path: Path) -> Path:
    return get_mock_examples_dir(home_path) / MOCK_EXAMPLES_CONFIG_NAME


@pytest.fixture(autouse=True)
def _setup_mocks(mocker: MockerFixture, tmp_path: Path) -> MagicMock:
    """Sets up mocks for dependencies used by the example command."""
    mock_home = mocker.patch("pathlib.Path.home", return_value=tmp_path)

    # Define paths based on mocked home
    mock_examples_dir = get_mock_examples_dir(mock_home())
    mock_examples_config_path = get_mock_examples_config_path(mock_home())

    # Ensure constants point to mocked locations relative to tmp_path
    mocker.patch("algokit.core.init.ALGOKIT_USER_DIR", MOCK_USER_DIR_NAME)
    mocker.patch("algokit.cli.init.example.ALGOKIT_USER_DIR", MOCK_USER_DIR_NAME)

    mocker.patch("algokit.core.init.ALGOKIT_TEMPLATES_DIR", MOCK_TEMPLATES_DIR_NAME)
    mocker.patch("algokit.cli.init.example.ALGOKIT_TEMPLATES_DIR", MOCK_TEMPLATES_DIR_NAME)

    # Mock _manage_templates_repository
    mocker.patch("algokit.cli.init.example._manage_templates_repository")

    # Mock _load_algokit_examples to return mock data and check correct path is used
    def _mock_load_examples(config_path: str) -> list[dict]:
        assert Path(config_path) == mock_examples_config_path
        return MOCK_EXAMPLES

    mocker.patch("algokit.cli.init.example._load_algokit_examples", side_effect=_mock_load_examples)

    # Mock _open_ide
    mocker.patch("algokit.cli.init.example._open_ide")

    # Mock shutil.copytree
    mocker.patch("algokit.cli.init.example.shutil.copytree")

    # Mock git availability
    which_mock = WhichMock()
    which_mock.add("git")
    mocker.patch("algokit.cli.init.example.shutil.which").side_effect = which_mock.which

    # Mock ExampleSelector TUI App
    mock_example_selector_instance = MagicMock()
    # Configure default behavior (can be overridden per test)
    mock_example_selector_instance.user_answers = {}
    mock_example_selector_class = mocker.patch("algokit.cli.init.example.ExampleSelector")
    mock_example_selector_class.return_value = mock_example_selector_instance
    # Mock the config path used by the TUI module itself
    mocker.patch(
        "algokit.cli.tui.init.example_selector.examples_config_path",
        str(mock_examples_config_path.absolute()),
    )

    # Create mock source directories within the mocked ~/.algokit/templates/examples
    for example in MOCK_EXAMPLES:
        example_src_path = mock_examples_dir / example["id"]
        example_src_path.mkdir(parents=True, exist_ok=True)
        (example_src_path / "readme.md").touch()  # Add a dummy file

    # Return the mocked selector instance for potential customization in tests
    return mock_example_selector_instance


@pytest.fixture
def cwd(tmp_path: Path) -> Path:
    """Provides the temporary working directory for tests."""
    # Use a sub-directory within tmp_path to avoid conflicts with mocked home
    test_cwd = tmp_path / "test_cwd"
    test_cwd.mkdir()
    return test_cwd


def test_example_command_help() -> None:
    result = invoke("init example -h")
    assert result.exit_code == 0
    verify(result.output)


def test_example_command_with_valid_id(mocker: MockerFixture, cwd: Path) -> None:
    example_id = "react-vite"
    mock_copytree = mocker.patch("algokit.cli.init.example.shutil.copytree")
    mock_open_ide = mocker.patch("algokit.cli.init.example._open_ide")
    home_path = Path.home()
    expected_src = get_mock_examples_dir(home_path) / example_id
    expected_dest = cwd / example_id

    result = invoke(["init", "example", example_id], cwd=cwd)

    assert result.exit_code == 0
    assert f"Created example {example_id}" in result.output
    mock_copytree.assert_called_once_with(expected_src, expected_dest)
    mock_open_ide.assert_called_once_with(expected_dest)
    verify(result.output)


def test_example_command_with_invalid_id(mocker: MockerFixture, cwd: Path) -> None:
    example_id = "nonexistent"
    mock_copytree = mocker.patch("algokit.cli.init.example.shutil.copytree")
    mock_open_ide = mocker.patch("algokit.cli.init.example._open_ide")

    result = invoke(["init", "example", example_id], cwd=cwd)

    assert result.exit_code == 0
    assert f"Example {example_id} not found" in result.output
    assert "Available example ids:" in result.output
    for example in MOCK_EXAMPLES:
        assert f"  {example['id']}" in result.output
    mock_copytree.assert_not_called()
    mock_open_ide.assert_not_called()
    verify(result.output)


def test_example_command_with_valid_id_source_not_exist(mocker: MockerFixture, cwd: Path) -> None:
    example_id = "react-vite"
    home_path = Path.home()
    example_src_path = get_mock_examples_dir(home_path) / example_id

    # Ensure the source directory doesn't exist for this test
    if example_src_path.exists():
        shutil.rmtree(example_src_path)

    mock_copytree = mocker.patch("algokit.cli.init.example.shutil.copytree")
    mock_open_ide = mocker.patch("algokit.cli.init.example._open_ide")

    result = invoke(["init", "example", example_id], cwd=cwd)

    assert result.exit_code == 0  # Command exits cleanly after printing error
    assert f"Example {example_id} not found" in result.output
    # Should not list available IDs if the ID was valid but source dir missing
    assert "Available example ids:" not in result.output
    mock_copytree.assert_not_called()
    mock_open_ide.assert_not_called()
    verify(result.output)


def test_example_command_with_valid_id_target_exists(mocker: MockerFixture, cwd: Path) -> None:
    example_id = "react-vite"
    mock_copytree = mocker.patch("algokit.cli.init.example.shutil.copytree")
    mock_open_ide = mocker.patch("algokit.cli.init.example._open_ide")
    home_path = Path.home()
    expected_src = get_mock_examples_dir(home_path) / example_id
    expected_dest = cwd / example_id

    # Pre-create the target directory
    expected_dest.mkdir()

    # Make copytree raise error if target exists (default behavior)
    mock_copytree.side_effect = FileExistsError("Target exists")

    result = invoke(["init", "example", example_id], cwd=cwd)

    # Expecting failure because shutil.copytree fails if dest exists
    assert result.exit_code == 1
    assert isinstance(result.exception, FileExistsError)
    mock_copytree.assert_called_once_with(expected_src, expected_dest)
    mock_open_ide.assert_not_called()


def test_example_command_tui_select_valid(mocker: MockerFixture, cwd: Path) -> None:
    selected_example_id = "python-smart-contract"

    # Get the mock instance from the fixture
    mock_example_selector = mocker.patch("algokit.cli.init.example.ExampleSelector").return_value
    # Configure the mocked selector instance to return the selected ID
    mock_example_selector.user_answers = {"example_id": selected_example_id}

    mock_copytree = mocker.patch("algokit.cli.init.example.shutil.copytree")
    mock_open_ide = mocker.patch("algokit.cli.init.example._open_ide")
    home_path = Path.home()
    expected_src = get_mock_examples_dir(home_path) / selected_example_id
    expected_dest = cwd / selected_example_id

    result = invoke("init example", cwd=cwd)

    assert result.exit_code == 0
    mock_example_selector.run.assert_called_once()
    assert f"Created example {selected_example_id}" in result.output
    mock_copytree.assert_called_once_with(expected_src, expected_dest)
    mock_open_ide.assert_called_once_with(expected_dest)
    verify(result.output)


def test_example_command_tui_select_nothing(mocker: MockerFixture, cwd: Path) -> None:
    # Get the mock instance from the fixture
    mock_example_selector = mocker.patch("algokit.cli.init.example.ExampleSelector").return_value
    # Ensure the mocked selector returns no selection
    mock_example_selector.user_answers = {}

    mock_copytree = mocker.patch("algokit.cli.init.example.shutil.copytree")
    mock_open_ide = mocker.patch("algokit.cli.init.example._open_ide")

    result = invoke("init example", cwd=cwd)

    assert result.exit_code == 0  # Command exits cleanly
    mock_example_selector.run.assert_called_once()
    # Assert that no 'Created example' message appears and no copy/IDE open happened
    assert "Created example" not in result.output
    mock_copytree.assert_not_called()
    mock_open_ide.assert_not_called()
    verify(result.output)


def test_example_command_tui_select_valid_but_source_missing(mocker: MockerFixture, cwd: Path) -> None:
    selected_example_id = "python-smart-contract"

    # Get the mock instance from the fixture
    mock_example_selector = mocker.patch("algokit.cli.init.example.ExampleSelector").return_value
    # Configure the mocked selector instance to return the selected ID
    mock_example_selector.user_answers = {"example_id": selected_example_id}

    home_path = Path.home()
    example_src_path = get_mock_examples_dir(home_path) / selected_example_id
    # Ensure the source directory doesn't exist for this test
    if example_src_path.exists():
        shutil.rmtree(example_src_path)

    mock_copytree = mocker.patch("algokit.cli.init.example.shutil.copytree")
    mock_open_ide = mocker.patch("algokit.cli.init.example._open_ide")

    result = invoke("init example", cwd=cwd)

    assert result.exit_code == 0  # Command exits cleanly after printing error
    mock_example_selector.run.assert_called_once()
    assert f"Example {selected_example_id} not found" in result.output
    mock_copytree.assert_not_called()
    mock_open_ide.assert_not_called()
    verify(result.output)


def test_example_command_list_option(mocker: MockerFixture, cwd: Path) -> None:
    """Test that the --list option displays all available examples."""

    mock_copytree = mocker.patch("algokit.cli.init.example.shutil.copytree")
    mock_open_ide = mocker.patch("algokit.cli.init.example._open_ide")

    # Test with short flag
    result = invoke(["init", "example", "-l"], cwd=cwd)

    assert result.exit_code == 0
    assert "Available examples:" in result.output
    for example in MOCK_EXAMPLES:
        assert f"  {example['id']} - {example.get('name', '')}" in result.output
    mock_copytree.assert_not_called()
    mock_open_ide.assert_not_called()
    verify(result.output)

    # Test with long flag
    result = invoke(["init", "example", "--list"], cwd=cwd)

    assert result.exit_code == 0
    assert "Available examples:" in result.output
    for example in MOCK_EXAMPLES:
        assert f"  {example['id']} - {example.get('name', '')}" in result.output
    mock_copytree.assert_not_called()
    mock_open_ide.assert_not_called()
    verify(result.output)
