import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import click
import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.namer import NamerFactory
from approvaltests.pytest.py_test_namer import PyTestNamer
from approvaltests.scrubbers.scrubbers import Scrubber
from prompt_toolkit.input import PipeInput
from pytest_mock import MockerFixture

from algokit.core.init import append_project_to_vscode_workspace
from tests.utils.approvals import TokenScrubber, combine_scrubbers, verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock
from tests.utils.which_mock import WhichMock

PARENT_DIRECTORY = Path(__file__).parent
GIT_BUNDLE_PATH = PARENT_DIRECTORY / "copier-helloworld.bundle"


def _remove_git_hints(output: str) -> str:
    git_init_hint_prefix = "DEBUG: git: hint:"
    lines = [line for line in output.splitlines() if not line.startswith(git_init_hint_prefix)]
    return "\n".join(lines)


def _remove_project_paths(output: str) -> str:
    lines = [
        "DEBUG: Attempting to load project config from {current_working_directory}/.algokit.toml"
        if "DEBUG: Attempting to load project config from " in line
        else line
        for line in output.splitlines()
    ]

    return "\n".join(lines)


class MockPipeInput(str, Enum):
    LEFT = "\x1b[D"
    RIGHT = "\x1b[C"
    UP = "\x1b[A"
    DOWN = "\x1b[B"
    ENTER = "\n"


@dataclass
class MockQuestionaryAnswer:
    """
    Dummy class used to represent questionary answer with value indicating the question, and commands
    being an array of emulated inputs required to be sent to the questionary to pick the desired answer.
    """

    value: str
    commands: list[MockPipeInput]


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


@pytest.fixture(autouse=True)
def which_mock(mocker: MockerFixture) -> WhichMock:
    which_mock = WhichMock()
    which_mock.add("git")
    mocker.patch("algokit.cli.init.command.shutil.which").side_effect = which_mock.which
    return which_mock


class ExtendedTemplateKey(str, Enum):
    # Include all keys from TemplateKey and add new ones
    BASE = "base"
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    TEALSCRIPT = "tealscript"
    FULLSTACK = "fullstack"
    REACT = "react"
    PYTHON_WITH_VERSION = "python_with_version"
    SIMPLE = "simple"


# Define a fixture to monkeypatch TemplateKey with ExtendedTemplateKey
@pytest.fixture(autouse=True)
def _set_mocked_template_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("algokit.cli.init.command.TemplateKey", ExtendedTemplateKey)


@pytest.fixture(autouse=True)
def _set_blessed_templates(mocker: MockerFixture) -> None:
    from algokit.cli.init import init_group
    from algokit.cli.init.helpers import BlessedTemplateSource

    blessed_templates = {
        ExtendedTemplateKey.SIMPLE: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-base-template",
            description="Does nothing helpful. simple",
        ),
        ExtendedTemplateKey.PYTHON_WITH_VERSION: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-python-template",
            commit="f97be2c0e3975adfaeb16ef07a2b4bd6ce2afcff",
            description="Provides a good starting point to build python smart contracts productively, but pinned.",
        ),
        ExtendedTemplateKey.FULLSTACK: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-base-template",
            description="Does nothing helpful. fullstack",
        ),
        ExtendedTemplateKey.PYTHON: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-python-template",
            description="Does nothing helpful. python",
        ),
        ExtendedTemplateKey.REACT: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-base-template",
            description="Does nothing helpful. react",
        ),
        ExtendedTemplateKey.BASE: BlessedTemplateSource(
            url="gh:algorandfoundation/algokit-base-template",
            description="Does nothing helpful. base",
        ),
    }

    (template_param,) = (p for p in init_group.params if p.name == "template_name")
    template_param.type = click.Choice(list(blessed_templates))

    mocker.patch("algokit.cli.init.command._get_blessed_templates").return_value = blessed_templates


@pytest.fixture(autouse=True)
def _override_bootstrap(mocker: MockerFixture) -> None:
    def bootstrap_mock(p: Path, *, ci_mode: bool, max_depth: int = 1) -> None:  # noqa: ARG001
        click.echo(f"Executed `algokit project bootstrap all` in {p}")

    mocker.patch("algokit.cli.init.command.bootstrap_any_including_subdirs").side_effect = bootstrap_mock


def test_init_help() -> None:
    result = invoke("init -h")

    assert result.exit_code == 0
    verify(result.output)


def test_init_missing_git(which_mock: WhichMock) -> None:
    which_mock.remove("git")
    result = invoke("init")

    assert result.exit_code != 0
    verify(result.output, scrubber=make_output_scrubber())


def test_invalid_name() -> None:
    result = invoke("init --name invalid{name")

    assert result.exit_code != 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_no_interaction_required_no_git_no_network(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url "
        "--answer project_name test --answer greeting hi --answer include_extra_file yes --bootstrap --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path("myapp"),
        Path("myapp") / "test",
        Path("myapp") / "test" / "extra_file.txt",
        Path("myapp") / "test" / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_no_interaction_required_no_git_no_network_with_vscode(
    tmp_path_factory: TempPathFactory,
    proc_mock: ProcMock,
    mock_questionary_input: PipeInput,
    which_mock: WhichMock,
    request: pytest.FixtureRequest,
) -> None:
    code_cmd = which_mock.add("code")
    proc_mock.set_output([code_cmd], ["Launch project"])

    cwd = tmp_path_factory.mktemp("cwd")
    app_name = "myapp"
    project_path = cwd / app_name
    (project_path / ".vscode").mkdir(parents=True)
    mock_questionary_input.send_text("Y")  # reuse existing directory

    result = invoke(
        f"init --name {app_name} --no-git --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url "
        "--answer project_name test --answer greeting hi --answer include_extra_file yes --bootstrap --no-workspace",
        cwd=cwd,
    )
    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber(), namer=PyTestNamer(request))


def test_init_no_interaction_required_no_git_no_network_with_vscode_and_readme(
    tmp_path_factory: TempPathFactory, proc_mock: ProcMock, mock_questionary_input: PipeInput, which_mock: WhichMock
) -> None:
    code_cmd = which_mock.add("code")
    proc_mock.set_output([code_cmd], ["Launch project"])

    cwd = tmp_path_factory.mktemp("cwd")
    app_name = "myapp"
    project_path = cwd / app_name
    (project_path / ".vscode").mkdir(parents=True)
    (project_path / "README.txt").touch()
    mock_questionary_input.send_text("Y")  # reuse existing directory

    result = invoke(
        f"init --name {app_name} --no-git --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url "
        "--answer project_name test --answer greeting hi --answer include_extra_file yes --bootstrap --no-workspace",
        cwd=cwd,
    )
    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_no_interaction_required_no_git_no_network_with_no_ide(
    tmp_path_factory: TempPathFactory,
    proc_mock: ProcMock,
    mock_questionary_input: PipeInput,
    which_mock: WhichMock,
) -> None:
    code_cmd = which_mock.add("code")
    proc_mock.should_fail_on(code_cmd)

    cwd = tmp_path_factory.mktemp("cwd")
    app_name = "myapp"
    project_path = cwd / app_name

    (project_path / ".vscode").mkdir(parents=True)
    mock_questionary_input.send_text("Y")  # reuse existing directory

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' "
        "--UNSAFE-SECURITY-accept-template-url "
        "--answer project_name test --answer greeting hi --answer include_extra_file yes "
        "--bootstrap --no-ide --no-workspace",
        cwd=cwd,
    )
    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_no_interaction_required_defaults_no_git_no_network(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        f"init --name myapp --no-git --defaults "
        f"--template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path("myapp"),
        Path("myapp") / "myapp",
        Path("myapp") / "myapp" / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_minimal_interaction_required_no_git_no_network_no_bootstrap(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    # Accept community template
    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults --no-bootstrap --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path("myapp"),
        Path("myapp") / "myapp",
        Path("myapp") / "myapp" / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_minimal_interaction_required_yes_git_no_network(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")
    dir_name = "myapp"
    result = invoke(
        f"init --name {dir_name} --git --template-url '{GIT_BUNDLE_PATH}' --defaults --no-workspace",
        cwd=cwd,
        env={
            "GIT_AUTHOR_NAME": "GitHub Actions",
            "GIT_COMMITTER_NAME": "GitHub Actions",
            "GIT_AUTHOR_EMAIL": "no-reply@example.com",
            "GIT_COMMITTER_EMAIL": "no-reply@example.com",
        },
    )

    assert result.exit_code == 0
    created_dir = cwd / dir_name
    assert created_dir.is_dir()
    paths = {p.relative_to(created_dir) for p in created_dir.iterdir()}
    assert paths == {Path(".git"), Path("myapp")}
    git_rev_list = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"], cwd=created_dir, capture_output=True, text=True, check=False
    )
    assert git_rev_list.returncode == 0
    git_initial_commit_hash = git_rev_list.stdout[:7]
    verify(
        result.output,
        scrubber=make_output_scrubber(_remove_git_hints, git_initial_commit_hash=git_initial_commit_hash),
    )


def test_init_do_not_use_existing_folder(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / "myapp").mkdir()
    mock_questionary_input.send_text("N")

    result = invoke(
        "init --name myapp --no-git --defaults"
        f" --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_use_existing_folder(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / "myapp").mkdir()
    mock_questionary_input.send_text("Y")  # override

    result = invoke(
        "init --name myapp --no-git --defaults"
        f" --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_existing_filename_same_as_folder_name(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "myapp").touch()

    mock_questionary_input.send_text("Y")  # override

    result = invoke(
        "init --name myapp --no-git --defaults "
        f"--template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_template_selection(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    mock_questionary_input.send_text("\n\n\n")
    result = invoke(
        "init --name myapp --no-git --defaults --no-workspace",
        cwd=cwd,
    )
    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_invalid_template_url(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")  # community warning
    result = invoke(
        "init --name myapp --no-git --template-url https://www.google.com --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_project_name(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    project_name = "FAKE_PROJECT"
    mock_questionary_input.send_text(project_name + "\n")
    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init --no-git --defaults --template-url '{GIT_BUNDLE_PATH}' "
        f"--UNSAFE-SECURITY-accept-template-url --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path(project_name),
        Path(project_name) / project_name,
        Path(project_name) / project_name / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_bootstrap_yes(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init -n myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url"
        " --answer greeting hi --answer include_extra_file yes --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_bootstrap_no(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    mock_questionary_input.send_text("N")
    result = invoke(
        f"init -n myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url"
        " --answer greeting hi --answer include_extra_file yes --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_project_name_not_empty(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    project_name = "FAKE_PROJECT"
    mock_questionary_input.send_text("\n")
    mock_questionary_input.send_text(project_name + "\n")
    command = (
        f"init --no-git --template-url '{GIT_BUNDLE_PATH}' "
        "--UNSAFE-SECURITY-accept-template-url --defaults --no-workspace"
    )
    result = invoke(command, cwd=cwd)

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path(project_name),
        Path(project_name) / project_name,
        Path(project_name) / project_name / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_project_name_reenter_folder_name(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    project_name = "FAKE_PROJECT"
    (cwd / project_name).mkdir()

    mock_questionary_input.send_text(project_name + "\n")
    mock_questionary_input.send_text("N")
    project_name_2 = "FAKE_PROJECT_2"
    mock_questionary_input.send_text(project_name_2 + "\n")
    command = (
        f"init --no-git --template-url '{GIT_BUNDLE_PATH}' "
        "--UNSAFE-SECURITY-accept-template-url --defaults --no-workspace"
    )
    result = invoke(command, cwd=cwd)

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path(project_name_2),
        Path(project_name_2) / project_name_2,
        Path(project_name_2) / project_name_2 / "helloworld.txt",
        Path(project_name),
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_ask_about_git(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")  # community one
    mock_questionary_input.send_text("Y")  # git
    dir_name = "myapp"
    result = invoke(
        f"init --name myapp --template-url '{GIT_BUNDLE_PATH}' --defaults --no-workspace",
        cwd=cwd,
        env={
            "GIT_AUTHOR_NAME": "GitHub Actions",
            "GIT_COMMITTER_NAME": "GitHub Actions",
            "GIT_AUTHOR_EMAIL": "no-reply@example.com",
            "GIT_COMMITTER_EMAIL": "no-reply@example.com",
        },
    )

    assert result.exit_code == 0
    created_dir = cwd / dir_name
    assert created_dir.is_dir()
    paths = {p.relative_to(created_dir) for p in created_dir.iterdir()}
    assert paths == {Path("myapp"), Path(".git")}
    git_rev_list = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"], cwd=created_dir, capture_output=True, text=True, check=False
    )
    assert git_rev_list.returncode == 0
    git_initial_commit_hash = git_rev_list.stdout[:7]
    verify(
        result.output,
        scrubber=make_output_scrubber(_remove_git_hints, git_initial_commit_hash=git_initial_commit_hash),
    )


def test_init_template_url_and_template_name(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")  # community warning
    result = invoke(
        f"init --name myapp --no-git --template simple --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.usefixtures("mock_questionary_input")
def test_init_template_url_and_ref(tmp_path_factory: TempPathFactory, mocker: MockerFixture) -> None:
    mock_copier_worker_cls = mocker.patch("copier._main.Worker")
    mock_copier_worker_cls.return_value.__enter__.return_value.template.url_expanded = "URL"
    ref = "abcdef123456"
    cwd = tmp_path_factory.mktemp("cwd")
    result = invoke(
        "init --name myapp --no-git --no-bootstrap "
        "--template-url gh:algorandfoundation/algokit-python-template "
        f"--template-url-ref {ref} "
        "--UNSAFE-SECURITY-accept-template-url --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    assert mock_copier_worker_cls.call_args.kwargs["vcs_ref"] == ref


def test_init_blessed_template_url_get_community_warning(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("N")  # community warning
    result = invoke(
        "init --name myapp --no-git "
        "--template-url gh:algorandfoundation/algokit-python-template --defaults "
        "-a author_name None -a author_email None ",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_with_any_template_url_get_community_warning(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    mock_questionary_input.send_text("Y")
    result = invoke(
        "init --name myapp --no-git --no-bootstrap "
        "--template-url gh:algorandfoundation/algokit-python-template --defaults --no-workspace "
        "-a author_name None -a author_email None ",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths.issuperset(
        {
            Path("myapp"),
            Path("myapp") / "README.md",
            Path("myapp") / "smart_contracts",
        }
    )
    verify(
        result.output,
        scrubber=make_output_scrubber(),
    )


def test_init_with_any_template_url_get_community_warning_with_unsafe_tag(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    result = invoke(
        "init --name myapp --no-git --no-bootstrap "
        "--template-url gh:algorandfoundation/algokit-python-template --defaults --no-workspace "
        "-a author_name None -a author_email None --UNSAFE-SECURITY-accept-template-url",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths.issuperset(
        {
            Path("myapp"),
            Path("myapp") / "README.md",
            Path("myapp") / "smart_contracts",
        }
    )
    verify(
        result.output,
        scrubber=make_output_scrubber(),
    )


def test_init_no_community_template(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("N")  # community warning
    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_input_template_url(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    # Source for special keys https://github.com/tmbo/questionary/blob/master/tests/prompts/test_select.py
    mock_questionary_input.send_text("\x1b[A")  # one up
    mock_questionary_input.send_text("\n")  # enter

    mock_questionary_input.send_text(str(GIT_BUNDLE_PATH) + "\n")  # name
    result = invoke(
        "init --name myapp --no-git --defaults --no-workspace",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_with_official_template_name(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "init --name myapp --no-git --no-bootstrap --template python --defaults --no-workspace "
        "-a author_name None -a author_email None ",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths.issuperset(
        {
            Path("myapp"),
            Path("myapp") / "README.md",
            Path("myapp") / "smart_contracts",
        }
    )
    verify(
        result.output,
        scrubber=make_output_scrubber(),
    )


def test_init_with_official_template_name_and_hash(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "init --name myapp --no-git --template python_with_version"
        " --defaults -a run_poetry_install False -a author_name None -a author_email None --no-workspace ",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths.issuperset(
        {
            Path("myapp"),
            Path("myapp") / "README.md",
            Path("myapp") / "smart_contracts",
        }
    )
    verify(result.output, scrubber=make_output_scrubber())


def test_init_with_custom_env(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        (
            "init --name myapp --no-git --no-bootstrap --template python --defaults --no-workspace "
            "-a author_name None -a author_email None "
            '-a algod_token "abcdefghijklmnopqrstuvwxyz" -a algod_server http://mylocalserver -a algod_port 1234 '
            '-a indexer_token "zyxwvutsrqponmlkjihgfedcba" -a indexer_server http://myotherserver -a indexer_port 6789 '
            " -a run_poetry_install False"
        ),
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths.issuperset(
        {
            Path("myapp"),
            Path("myapp") / "README.md",
            Path("myapp") / "smart_contracts",
        }
    )

    verify(
        result.output,
        scrubber=make_output_scrubber(),
    )


def test_init_template_with_python_task_fails_on_missing_python(
    mocker: MockerFixture, dummy_algokit_template_with_python_task: dict[str, Path]
) -> None:
    which_mock = WhichMock()
    mocker.patch("algokit.core.utils.which").side_effect = which_mock.which
    mocker.patch("algokit.core.utils.get_base_python_path", return_value=None)
    which_mock.remove("python")
    which_mock.remove("python3")

    ref = "HEAD"
    result = invoke(
        [
            "init",
            "--name",
            "myapp",
            "--no-git",
            "--defaults",
            f"--template-url={dummy_algokit_template_with_python_task['template_path']}",
            f"--template-url-ref={ref}",
            "--UNSAFE-SECURITY-accept-template-url",
            "--no-workspace",
        ],
        cwd=dummy_algokit_template_with_python_task["cwd"],
        input="y\n",
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_template_with_python_task_works(dummy_algokit_template_with_python_task: dict[str, Path]) -> None:
    ref = "HEAD"
    result = invoke(
        [
            "init",
            "--name",
            "myapp",
            "--no-git",
            "--defaults",
            f"--template-url={dummy_algokit_template_with_python_task['template_path']}",
            f"--template-url-ref={ref}",
            "--UNSAFE-SECURITY-accept-template-url",
            "--no-workspace",
        ],
        cwd=dummy_algokit_template_with_python_task["cwd"],
        input="y\n",
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.parametrize(
    ("flow_steps"),
    [
        [
            MockQuestionaryAnswer("Smart Contract", [MockPipeInput.ENTER, MockPipeInput.ENTER]),
            None,  # no custom template URL
        ],
        [
            MockQuestionaryAnswer("DApp Frontend", [MockPipeInput.DOWN, MockPipeInput.ENTER]),
            None,  # no custom template URL
        ],
        [
            MockQuestionaryAnswer(
                "Full Stack", [MockPipeInput.DOWN, MockPipeInput.DOWN, MockPipeInput.ENTER, MockPipeInput.ENTER]
            ),
            None,  # no custom template URL
        ],
        [
            MockQuestionaryAnswer("Custom Template", [MockPipeInput.UP, MockPipeInput.ENTER]),
            "gh:algorandfoundation/algokit-base-template\n",  # custom template URL
        ],
    ],
)
def test_init_wizard_v2_flow(
    flow_steps: list, tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    for step in flow_steps:
        if isinstance(step, MockQuestionaryAnswer):
            for command in step.commands:
                mock_questionary_input.send_text(command.value)
        elif isinstance(step, str):
            mock_questionary_input.send_text(step)

    # Act
    result = invoke("init --defaults --no-git --name myapp --UNSAFE-SECURITY-accept-template-url", cwd=cwd)

    # Assert
    project_type = flow_steps[0].value  # The first step always determines the project type
    assert result.exit_code == 0
    verify(
        result.output,
        options=NamerFactory.with_parameters(project_type),
        scrubber=make_output_scrubber(),
    )


def test_init_wizard_v2_workspace_nesting(
    tmp_path_factory: TempPathFactory,
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")

    # Act
    project_a_result = invoke(
        "init -t python --no-git --defaults --name myapp "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'production'",
        cwd=cwd,
    )
    project_b_result = invoke(
        "init -t python --no-git --defaults --name myapp2 "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'starter'",
        cwd=cwd / "myapp" / "projects",
    )
    project_c_result = invoke(
        "init -t python --no-git --defaults --name myapp3 "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'starter' --no-workspace",
        cwd=cwd / "myapp" / "projects",
    )
    project_d_result = invoke(
        "init -t python --no-git --defaults --name myapp4 "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'starter'",
        cwd=cwd / "myapp",
    )

    # Assert
    assert project_a_result.exit_code == 0
    assert project_b_result.exit_code == 1
    assert project_c_result.exit_code == 0
    assert project_d_result.exit_code == 0


def test_init_wizard_v2_github_folder_with_workspace(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    answer = MockQuestionaryAnswer("Smart Contract", [MockPipeInput.ENTER, MockPipeInput.ENTER])
    for command in answer.commands:
        mock_questionary_input.send_text(command.value)

    # Act
    result = invoke(
        "init -t python --no-git --defaults --name myapp "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'production'",
        cwd=cwd,
    )

    # Assert
    cwd /= "myapp"
    assert result.exit_code == 0
    assert not cwd.joinpath("projects/myapp/.github").exists()
    assert cwd.joinpath(".github").exists()
    assert cwd.glob(".github/workflows/*.yaml")


def test_init_wizard_v2_github_folder_with_workspace_partial(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    mock_questionary_input.send_text("y\n")  # Simulate workspace selection

    github_workflow_path = cwd / "myapp" / ".github" / "workflows"
    github_workflow_path.mkdir(parents=True, exist_ok=True)
    (github_workflow_path / "cd.yaml").touch()

    # Act
    result = invoke(
        "init -t python --no-git --defaults --name myapp "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'production'",
        input="y\n",
        cwd=cwd,
    )

    # Assert
    cwd /= "myapp"
    assert result.exit_code == 0
    assert not (cwd / "projects/myapp/.github/workflows/cd.yaml").exists()
    assert (cwd / ".github/workflows/myapp-cd.yaml").read_text() != ""
    assert cwd.glob(".github/workflows/*.yaml")


def test_init_wizard_v2_github_folder_no_workspace(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    answer = MockQuestionaryAnswer("Smart Contract", [MockPipeInput.ENTER, MockPipeInput.ENTER])
    for command in answer.commands:
        mock_questionary_input.send_text(command.value)

    # Act
    result = invoke(
        "init -t python --no-git --defaults --name myapp "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'production' --no-workspace",
        cwd=cwd,
    )

    # Assert
    cwd /= "myapp"
    assert result.exit_code == 0
    assert not cwd.joinpath("projects").exists()
    assert cwd.joinpath(".github").exists()
    assert cwd.glob(".github/workflows/*.yaml")


@pytest.mark.parametrize(
    ("workspace_content", "expected_path", "expect_warning"),
    [
        # Scenario 1: Valid codespace, new project added
        (
            """
        {
          "folders": [
            {
              "path": ".",
              "name": "ROOT"
            },
            {
              "path": "projects/myapp"
            }
          ]
        }
        """,
            "projects/myapp2",
            False,
        ),
        # Scenario 2: No codespace, nothing happens
        (None, None, False),
        # Scenario 3: Invalid codespace, warning expected
        ("INVALID_JSON", None, True),
    ],
)
def test_init_wizard_v2_append_to_vscode_workspace(
    *,
    which_mock: WhichMock,
    proc_mock: ProcMock,
    tmp_path_factory: TempPathFactory,
    mock_questionary_input: PipeInput,
    workspace_content: str,
    expected_path: str,
    expect_warning: bool,
) -> None:
    # Arrange
    code_cmd = which_mock.add("code")
    proc_mock.set_output([code_cmd], ["Launch project"])

    cwd = tmp_path_factory.mktemp("cwd")
    answer = MockQuestionaryAnswer("Smart Contract", [MockPipeInput.ENTER, MockPipeInput.ENTER])
    for command in answer.commands:
        mock_questionary_input.send_text(command.value)

    # Act
    project_a_result = invoke(
        "init -t python --no-git --defaults --name myapp "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'production'",
        cwd=cwd,
    )
    if workspace_content is not None:
        workspace_file = cwd / "myapp" / "myapp.code-workspace"
        workspace_file.write_text(workspace_content)

    project_b_result = invoke(
        "init -t python --no-git --defaults --name myapp2 "
        "--UNSAFE-SECURITY-accept-template-url -a preset_name 'starter'",
        cwd=cwd / "myapp",
    )

    # Assert
    assert project_a_result.exit_code == 0
    assert project_b_result.exit_code == 0
    if expected_path and "workspace_file" in locals():
        workspace_data = json.loads(workspace_file.read_text())
        assert workspace_data["folders"][-1]["path"] == expected_path
    if expect_warning:
        # This assumes the existence of a function `verify` to check for warnings in the output
        verify(project_b_result.output)


@pytest.mark.parametrize(
    ("initial_workspace", "project_path", "expected_workspace", "should_append"),
    [
        # Test case 1: Different representations of root path
        (
            {"folders": [{"path": "./"}]},
            ".",
            {"folders": [{"path": "./"}]},
            False,
        ),
        # Test case 2: Normalized paths
        (
            {"folders": [{"path": "projects/app1"}]},
            "projects/app1",
            {"folders": [{"path": "projects/app1"}]},
            False,
        ),
        # Test case 3: Different path separators
        (
            {"folders": [{"path": "projects\\app1"}]},
            "projects/app1",
            {"folders": [{"path": "projects\\app1"}]},
            False,
        ),
        # Test case 4: Relative paths
        (
            {"folders": [{"path": "./projects/app1"}]},
            "projects/app1",
            {"folders": [{"path": "./projects/app1"}]},
            False,
        ),
        # Test case 5: New unique path
        (
            {"folders": [{"path": "projects/app1"}]},
            "projects/app2",
            {"folders": [{"path": "projects/app1"}, {"path": "projects/app2"}]},
            True,
        ),
        # Test case 6: Empty workspace
        (
            {"folders": []},
            "projects/app1",
            {"folders": [{"path": "projects/app1"}]},
            True,
        ),
        # Test case 7: Path with trailing slash
        (
            {"folders": [{"path": "projects/app1/"}]},
            "projects/app1",
            {"folders": [{"path": "projects/app1/"}]},
            False,
        ),
    ],
)
def test_append_to_workspace_path_normalization(
    *,
    tmp_path_factory: pytest.TempPathFactory,
    initial_workspace: dict,
    project_path: str,
    expected_workspace: dict,
    should_append: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test various path normalization scenarios when appending to workspace."""

    # Arrange
    tmp_path = tmp_path_factory.mktemp("workspace")
    workspace_file = tmp_path / "test.code-workspace"
    with workspace_file.open(mode="w", encoding="utf-8") as f:
        json.dump(initial_workspace, f)

    project_path_obj = tmp_path / project_path
    project_path_obj.mkdir(parents=True, exist_ok=True)

    # Act
    append_project_to_vscode_workspace(project_path_obj, workspace_file)

    # Assert
    with workspace_file.open(mode="r", encoding="utf-8") as f:
        actual_workspace = json.load(f)

    assert actual_workspace == expected_workspace

    # Check logging
    debug_messages = [r.message for r in caplog.records if r.levelname == "DEBUG"]
    if should_append:
        assert any("Appended project" in msg for msg in debug_messages)
    else:
        assert any("already in workspace" in msg for msg in debug_messages)
