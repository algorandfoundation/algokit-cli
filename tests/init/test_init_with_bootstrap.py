from collections.abc import Callable
from pathlib import Path

import click
from _pytest.tmpdir import TempPathFactory
from approvaltests.scrubbers.scrubbers import Scrubber
from prompt_toolkit.input import PipeInput

from tests.utils.approvals import TokenScrubber, combine_scrubbers, verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock

PARENT_DIRECTORY = Path(__file__).parent
GIT_BUNDLE_PATH = PARENT_DIRECTORY / "copier-helloworld.bundle"


def make_output_scrubber(*extra_scrubbers: Callable[[str], str], **extra_tokens: str) -> Scrubber:
    default_tokens = {"test_parent_directory": str(PARENT_DIRECTORY)}
    tokens = default_tokens | extra_tokens
    return combine_scrubbers(
        *extra_scrubbers,
        click.unstyle,
        TokenScrubber(tokens=tokens),
        TokenScrubber(tokens={"test_parent_directory": str(PARENT_DIRECTORY).replace("\\", "/")}),
        lambda t: t.replace("{test_parent_directory}\\", "{test_parent_directory}/"),
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
        " --answer greeting hi --answer include_extra_file yes --bootstrap",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())
