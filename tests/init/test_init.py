from pathlib import Path
import logging

from _pytest.tmpdir import TempPathFactory
from approvaltests import verify
from prompt_toolkit.input import PipeInput
from utils.click_invoker import invoke
from click import unstyle

PARENT_DIRECTORY = Path(__file__).parent
GIT_BUNDLE_PATH = PARENT_DIRECTORY / "copier-script-v0.1.0.gitbundle"


def test_init_minimal_interaction_required_no_git_no_network(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
):
    cwd = tmp_path_factory.mktemp("cwd")

    logging.getLogger("plumbum.local").setLevel("INFO")
    logging.getLogger("asyncio").setLevel("INFO")
    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --answer script script.sh --answer nix yes",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {Path("myapp"), Path("myapp") / "script.sh"}
    verify(unstyle(result.output))
