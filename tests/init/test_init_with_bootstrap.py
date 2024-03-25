from collections.abc import Callable
from pathlib import Path

import click
from _pytest.tmpdir import TempPathFactory
from algokit.core.conf import ALGOKIT_CONFIG, get_current_package_version
from approvaltests.scrubbers.scrubbers import Scrubber
from prompt_toolkit.input import PipeInput

from tests.utils.approvals import TokenScrubber, combine_scrubbers, verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock

PARENT_DIRECTORY = Path(__file__).parent
GIT_BUNDLE_PATH = PARENT_DIRECTORY / "copier-helloworld.bundle"


def _remove_project_paths(output: str) -> str:
    lines = [
        "DEBUG: Attempting to load project config from {current_working_directory}/.algokit.toml"
        if "DEBUG: Attempting to load project config from " in line
        else line
        for line in output.splitlines()
    ]

    return "\n".join(lines)


def make_output_scrubber(*extra_scrubbers: Callable[[str], str], **extra_tokens: str) -> Scrubber:
    default_tokens = {"test_parent_directory": str(PARENT_DIRECTORY)}
    tokens = default_tokens | extra_tokens
    return combine_scrubbers(
        *extra_scrubbers,
        click.unstyle,
        TokenScrubber(tokens=tokens),
        TokenScrubber(tokens={"test_parent_directory": str(PARENT_DIRECTORY).replace("\\", "/")}),
        lambda t: t.replace("{test_parent_directory}\\", "{test_parent_directory}/"),
        _remove_project_paths,
    )


def test_init_bootstrap_broken_poetry(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput, proc_mock: ProcMock
) -> None:
    proc_mock.should_bad_exit_on("poetry --version")
    cwd = tmp_path_factory.mktemp("cwd")
    app_name = "myapp"
    project_path = cwd / app_name
    project_path.mkdir()
    (project_path / "poetry.toml").touch()
    mock_questionary_input.send_text("Y")  # reuse existing directory

    result = invoke(
        f"init -n {app_name} --no-git --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url"
        " --answer greeting hi --answer include_extra_file yes --bootstrap --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_bootstrap_version_fail(
    tmp_path_factory: TempPathFactory,
    mock_questionary_input: PipeInput,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    app_name = "myapp"
    project_path = cwd / app_name
    project_path.mkdir()
    (project_path / ALGOKIT_CONFIG).write_text('[algokit]\nmin_version = "999.99.99"\n')
    mock_questionary_input.send_text("Y")  # reuse existing directory

    result = invoke(
        f"init -n {app_name} --no-git --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url"
        " --answer greeting hi --answer include_extra_file yes --bootstrap --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber(current_version=get_current_package_version()))
