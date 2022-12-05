import logging
import subprocess
from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests import verify
from click import unstyle
from prompt_toolkit.input import PipeInput
from utils.click_invoker import invoke

PARENT_DIRECTORY = Path(__file__).parent
GIT_BUNDLE_PATH = PARENT_DIRECTORY / "copier-script-v0.1.0.gitbundle"


@pytest.fixture(autouse=True, scope="module")
def supress_copier_dependencies_debug_output():
    logging.getLogger("plumbum.local").setLevel("INFO")
    logging.getLogger("asyncio").setLevel("INFO")


def test_init_minimal_interaction_required_no_git_no_network(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --answer script script.sh --answer nix yes",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {Path("myapp"), Path("myapp") / "script.sh"}
    verify(unstyle(result.output).replace(str(PARENT_DIRECTORY), "{test_parent_directory}"))


def test_init_minimal_interaction_required_yes_git_no_network(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")
    dir_name = "myapp"
    result = invoke(
        f"init --name {dir_name} --git --template-url '{GIT_BUNDLE_PATH}' --answer script script.sh --answer nix yes",
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
    assert paths == {Path("script.sh"), Path(".git")}
    git_rev_list = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"], cwd=created_dir, capture_output=True, text=True
    )
    assert git_rev_list.returncode == 0
    git_initial_commit_hash = git_rev_list.stdout[:7]
    verify(
        unstyle(result.output)
        .replace(git_initial_commit_hash, "{git_initial_commit_hash}")
        .replace(str(PARENT_DIRECTORY), "{test_parent_directory}")
    )


def test_init_do_not_use_existing_folder(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / "myapp").mkdir()
    mock_questionary_input.send_text("N")

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --answer script script.sh --answer nix yes",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(unstyle(result.output).replace(str(PARENT_DIRECTORY), "{test_parent_directory}"))


def test_init_use_existing_folder(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / "myapp").mkdir()
    mock_questionary_input.send_text("Y")  # override
    mock_questionary_input.send_text("Y")  # community warning

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --answer script script.sh --answer nix yes",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(unstyle(result.output).replace(str(PARENT_DIRECTORY), "{test_parent_directory}"))


def test_init_existing_filename_same_as_folder_name(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
):
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "myapp").touch()

    mock_questionary_input.send_text("Y")  # override
    mock_questionary_input.send_text("Y")  # community warning

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --answer script script.sh --answer nix yes",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(unstyle(result.output).replace(str(PARENT_DIRECTORY), "{test_parent_directory}"))


def test_init_template_selection(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("\n")

    result = invoke(
        "init --name myapp --no-git --answer script script.sh --answer nix yes",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(unstyle(result.output).replace(str(PARENT_DIRECTORY), "{test_parent_directory}"))


def test_init_invalid_template_url(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")  # community warning
    result = invoke(
        "init --name myapp --no-git --template-url https://www.google.com --answer script script.sh --answer nix yes",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(unstyle(result.output).replace(str(PARENT_DIRECTORY), "{test_parent_directory}"))
