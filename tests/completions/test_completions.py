from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from algokit.cli.completions import SUPPORTED_SHELLS
from approvaltests.namer import NamerFactory
from pytest_mock import MockerFixture

from tests import get_combined_verify_output
from tests.utils.approvals import normalize_path, verify
from tests.utils.click_invoker import ClickInvokeResult, invoke

ORIGINAL_PROFILE_CONTENTS = "# ORIGINAL END OF FILE\n"


def test_completions_help() -> None:
    # Act
    result = invoke("completions")

    # Assert
    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.parametrize("command", ["install", "uninstall"])
def test_completions_subcommands_help(command: str) -> None:
    # Act
    result = invoke(f"completions {command} --help")

    # Assert
    assert result.exit_code == 0
    verify(result.output, options=NamerFactory.with_parameters(command))


def _mock_bash_version(mocker: MockerFixture, version: str) -> None:
    mocked_run = mocker.patch("subprocess.run")
    mocked_output = mocked_run.return_value
    mocked_output.configure_mock(stdout=version.encode())


@pytest.fixture(autouse=True)
def _mock_default_bash_version(mocker: MockerFixture) -> None:
    _mock_bash_version(mocker, "5.2.0")


class CompletionsTestContext:
    def __init__(self, expected_shell: str):
        self.home = TemporaryDirectory()
        self.home_path = Path(self.home.name).resolve()
        self.profile_path = self.home_path / f".{expected_shell}rc"
        self.config_path = self.home_path / ".config"
        self.source_path = self.config_path / "algokit" / f".algokit-completions.{expected_shell}"
        self.profile_path.write_text(ORIGINAL_PROFILE_CONTENTS)
        self.env = {
            # posix
            "HOME": str(self.home_path),
            "XDG_CONFIG_HOME": str(self.config_path),
            # windows
            "USERPROFILE": str(self.home_path),
            "APPDATA": str(self.config_path),
        }

    def run_command(self, command: str, shell: str | None = None) -> ClickInvokeResult:
        command = f"completions {command}"
        if shell:
            command += f" --shell {shell}"

        result = invoke(command, env=self.env)
        result.output = normalize_path(result.output, str(self.home_path), "{home}").replace("\\", "/")
        return result

    @property
    def profile_contents(self) -> str:
        return self.profile_path.read_text().replace("\\", "/")


@pytest.mark.parametrize("shell", SUPPORTED_SHELLS)
def test_completions_installs_correctly_with_specified_shell(shell: str) -> None:
    # Arrange
    context = CompletionsTestContext(shell)

    # Act
    result = context.run_command("install", shell)

    # Assert
    assert result.exit_code == 0
    # content of this file is defined by click, so only assert it exists not its content
    assert context.source_path.exists()
    assert not context.profile_path.with_suffix(".algokit~").exists()
    profile = context.profile_contents
    verify(get_combined_verify_output(result.output, "profile", profile), options=NamerFactory.with_parameters(shell))


def test_completions_installs_correctly_with_detected_shell(mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch("shellingham.detect_shell").return_value = ("bash", "/bin/bash")
    context = CompletionsTestContext("bash")

    # Act
    result = context.run_command("install")

    # Assert
    assert result.exit_code == 0
    # content of this file is defined by click, so only assert it exists not its content
    assert context.source_path.exists()
    profile = context.profile_contents
    verify(get_combined_verify_output(result.output, "profile", profile))


@pytest.mark.parametrize("shell", SUPPORTED_SHELLS)
def test_completions_uninstalls_correctly(shell: str) -> None:
    # Arrange
    context = CompletionsTestContext(shell)

    context.run_command("install", shell)

    # Act
    result = context.run_command("uninstall", shell)

    # Assert
    assert result.exit_code == 0
    assert not context.source_path.exists()
    profile = context.profile_contents
    assert not context.profile_path.with_suffix(".algokit~").exists()
    assert profile == ORIGINAL_PROFILE_CONTENTS
    verify(result.output, options=NamerFactory.with_parameters(shell))


@pytest.mark.parametrize("command", ["install", "uninstall"])
def test_completions_subcommands_with_unknown_shell_fails_gracefully(command: str, mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch("shellingham.detect_shell").return_value = None

    # Act
    result = invoke(f"completions {command}")

    # Assert
    assert result.exit_code == 1
    verify(result.output, options=NamerFactory.with_parameters(command))


@pytest.mark.parametrize("command", ["install", "uninstall"])
def test_completions_subcommands_with_unsupported_shell_fails_gracefully(command: str, mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch("shellingham.detect_shell").return_value = ("pwsh", "/bin/pwsh")

    # Act
    result = invoke(f"completions {command}")

    # Assert
    assert result.exit_code == 1
    verify(result.output, options=NamerFactory.with_parameters(command))


def test_completions_install_is_idempotent() -> None:
    # Arrange
    context = CompletionsTestContext("bash")
    context.run_command("install", "bash")

    # Act
    result = context.run_command("install", "bash")

    # Assert
    assert result.exit_code == 0
    # content of this file is defined by click, so only assert it exists not its content
    assert context.source_path.exists()
    profile = context.profile_contents
    verify(get_combined_verify_output(result.output, "profile", profile))


def test_completions_uninstall_is_idempotent() -> None:
    # Arrange
    context = CompletionsTestContext("bash")

    context.run_command("install", "bash")
    context.run_command("uninstall", "bash")

    # Act
    result = context.run_command("uninstall", "bash")

    # Assert
    assert result.exit_code == 0
    assert not context.source_path.exists()
    profile = context.profile_contents
    assert profile == ORIGINAL_PROFILE_CONTENTS
    verify(result.output)


def test_completions_install_handles_no_profile() -> None:
    # Arrange
    context = CompletionsTestContext("bash")
    context.profile_path.unlink()

    # Act
    result = context.run_command("install", "bash")

    # Assert
    assert result.exit_code == 0
    assert context.source_path.exists()
    profile = context.profile_contents
    verify(get_combined_verify_output(result.output, "profile", profile))


def test_completions_uninstall_handles_no_profile() -> None:
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


def test_completions_install_handles_config_outside_home() -> None:
    # Arrange
    context = CompletionsTestContext("bash")
    # create a different directory outside home directory for config
    config = TemporaryDirectory()
    context.config_path = Path(config.name).resolve()
    context.source_path = context.config_path / "algokit" / ".algokit-completions.bash"
    context.env["XDG_CONFIG_HOME"] = str(context.config_path)
    context.env["APPDATA"] = str(context.config_path)

    # Act
    result = context.run_command("install", "bash")

    # Assert
    assert result.exit_code == 0
    # content of this file is defined by click, so only assert it exists not its content
    assert context.source_path.exists()
    output = normalize_path(result.output, str(context.config_path), "{config}")
    profile = normalize_path(context.profile_contents, str(context.config_path), "{config}")
    verify(get_combined_verify_output(output, "profile", profile))


def test_completions_install_handles_unsupported_bash_gracefully(mocker: MockerFixture) -> None:
    # Arrange
    _mock_bash_version(mocker, "3.2.0")
    context = CompletionsTestContext("bash")

    # Act
    result = context.run_command("install", "bash")

    # Assert
    # NOTE: shellingham no longer throws an error when shell is not supported.
    # However, it still prints the error message to stderr.
    # Then it proceeds to try to install the completion script regardless.
    assert "Shell completion is not supported for Bash" in result.output
    assert context.source_path.exists()
