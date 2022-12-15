from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from algokit.cli.completions import SUPPORTED_SHELLS
from approvaltests.namer import NamerFactory
from pytest_mock import MockerFixture

from tests import get_combined_verify_output
from tests.utils.approvals import verify
from tests.utils.click_invoker import ClickInvokeResult, invoke

ORIGINAL_PROFILE_CONTENTS = "# ORIGINAL END OF FILE\n"


def test_completions_help():
    # Act
    result = invoke("completions")

    # Assert
    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.parametrize("command", ["install", "uninstall"])
def test_completions_subcommands_help(command: str):
    # Act
    result = invoke(f"completions {command} --help")

    # Assert
    assert result.exit_code == 0
    verify(result.output, options=NamerFactory.with_parameters(command))


class CompletionsTestContext:
    def __init__(self, expected_shell: str):
        self.home = TemporaryDirectory()
        self.home_path = Path(self.home.name)
        self.profile_path = self.home_path / f".{expected_shell}rc"
        self.source_path = self.home_path / ".config" / "algokit" / f".algokit-completions.{expected_shell}"
        self.profile_path.write_text(ORIGINAL_PROFILE_CONTENTS)
        self.env = {
            "HOME": self.home.name,
        }

    def run_command(self, command: str, shell: str | None = None) -> ClickInvokeResult:
        command = f"completions {command}"
        if shell:
            command += f" --shell {shell}"

        result = invoke(command, env=self.env)
        normalized_output = result.output.replace(self.home.name, "{home}")
        return ClickInvokeResult(exit_code=result.exit_code, output=normalized_output)


@pytest.mark.parametrize("shell", SUPPORTED_SHELLS)
def test_completions_installs_correctly_with_specified_shell(shell: str):
    # Arrange
    context = CompletionsTestContext(shell)

    # Act
    result = context.run_command("install", shell)

    # Assert
    assert result.exit_code == 0
    # content of this file is defined by click, so only assert it exists not its content
    assert context.source_path.exists()
    profile = context.profile_path.read_text()
    verify(get_combined_verify_output(result.output, "profile", profile), options=NamerFactory.with_parameters(shell))


def test_completions_installs_correctly_with_detected_shell(mocker: MockerFixture):
    # Arrange
    mocker.patch("shellingham.detect_shell").return_value = ("bash", "/bin/bash")
    context = CompletionsTestContext("bash")

    # Act
    result = context.run_command("install")

    # Assert
    assert result.exit_code == 0
    # content of this file is defined by click, so only assert it exists not its content
    assert context.source_path.exists()
    profile = context.profile_path.read_text()
    verify(get_combined_verify_output(result.output, "profile", profile))


@pytest.mark.parametrize("shell", SUPPORTED_SHELLS)
def test_completions_uninstalls_correctly(shell: str):
    # Arrange
    context = CompletionsTestContext(shell)

    context.run_command("install", shell)

    # Act
    result = context.run_command("uninstall", shell)

    # Assert
    assert result.exit_code == 0
    assert not context.source_path.exists()
    profile = context.profile_path.read_text()
    assert profile == ORIGINAL_PROFILE_CONTENTS
    verify(result.output, options=NamerFactory.with_parameters(shell))


@pytest.mark.parametrize("command", ["install", "uninstall"])
def test_completions_subcommands_with_unknown_shell_fails_gracefully(command: str, mocker: MockerFixture):
    # Arrange
    mocker.patch("shellingham.detect_shell").return_value = None

    # Act
    result = invoke(f"completions {command}")

    # Assert
    assert result.exit_code == 1
    verify(result.output, options=NamerFactory.with_parameters(command))


@pytest.mark.parametrize("command", ["install", "uninstall"])
def test_completions_subcommands_with_unsupported_shell_fails_gracefully(command: str, mocker: MockerFixture):
    # Arrange
    mocker.patch("shellingham.detect_shell").return_value = ("pwsh", "/bin/pwsh")

    # Act
    result = invoke(f"completions {command}")

    # Assert
    assert result.exit_code == 1
    verify(result.output, options=NamerFactory.with_parameters(command))


def test_completions_install_is_idempotent():
    # Arrange
    context = CompletionsTestContext("bash")
    context.run_command("install", "bash")

    # Act
    result = context.run_command("install", "bash")

    # Assert
    assert result.exit_code == 0
    # content of this file is defined by click, so only assert it exists not its content
    assert context.source_path.exists()
    profile = context.profile_path.read_text()
    verify(get_combined_verify_output(result.output, "profile", profile))


def test_completions_uninstall_is_idempotent():
    # Arrange
    context = CompletionsTestContext("bash")

    context.run_command("install", "bash")
    context.run_command("uninstall", "bash")

    # Act
    result = context.run_command("uninstall", "bash")

    # Assert
    assert result.exit_code == 0
    assert not context.source_path.exists()
    profile = context.profile_path.read_text()
    assert profile == ORIGINAL_PROFILE_CONTENTS
    verify(result.output)


def test_completions_install_handles_no_profile():
    # Arrange
    context = CompletionsTestContext("bash")
    context.profile_path.unlink()

    # Act
    result = context.run_command("install", "bash")

    # Assert
    assert result.exit_code == 0
    assert context.source_path.exists()
    profile = context.profile_path.read_text()
    verify(get_combined_verify_output(result.output, "profile", profile))


def test_completions_uninstall_handles_no_profile():
    # Arrange
    context = CompletionsTestContext("bash")
    context.run_command("install", "brew")
    context.profile_path.unlink()

    # Act
    result = context.run_command("uninstall", "bash")

    # Assert
    assert result.exit_code == 0
    assert not context.source_path.exists()
    assert not context.profile_path.exists()
    verify(result.output)


def test_completions_install_handles_config_outside_home():
    # Arrange
    context = CompletionsTestContext("bash")
    # create a different directory outside home directory for config
    context.config = TemporaryDirectory()
    context.source_path = Path(context.config.name) / "algokit" / ".algokit-completions.bash"
    context.env["XDG_CONFIG_HOME"] = context.config.name

    # Act
    result = context.run_command("install", "bash")

    # Assert
    assert result.exit_code == 0
    # content of this file is defined by click, so only assert it exists not its content
    assert context.source_path.exists()
    output = result.output.replace(context.config.name, "{config}")
    profile = context.profile_path.read_text().replace(context.config.name, "{config}")
    verify(get_combined_verify_output(output, "profile", profile))


def test_completions_install_handles_unsupported_bash_gracefully(mocker: MockerFixture):
    # Arrange
    mock_class = mocker.patch("click.shell_completion.get_completion_class").return_value
    mock_instance = mock_class.return_value
    mock_instance.source.side_effect = RuntimeError("Unsupported version")
    context = CompletionsTestContext("bash")

    # Act
    result = context.run_command("install", "bash")

    # Assert
    assert result.exit_code == 1
    assert not context.source_path.exists()
    verify(result.output)
