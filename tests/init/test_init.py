import logging
import subprocess
from pathlib import Path

import click
import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.scrubbers.scrubbers import Scrubber
from prompt_toolkit.input import PipeInput
from pytest_mock import MockerFixture
from utils.approvals import TokenScrubber, combine_scrubbers, verify
from utils.click_invoker import invoke

from tests import get_combined_verify_output

PARENT_DIRECTORY = Path(__file__).parent
GIT_BUNDLE_PATH = PARENT_DIRECTORY / "copier-helloworld.bundle"


def make_output_scrubber(**extra_tokens: str) -> Scrubber:
    default_tokens = {"test_parent_directory": str(PARENT_DIRECTORY)}
    tokens = default_tokens | extra_tokens
    return combine_scrubbers(
        click.unstyle,
        TokenScrubber(tokens=tokens),
        TokenScrubber(tokens={"test_parent_directory": str(PARENT_DIRECTORY).replace("\\", "/")}),
        lambda t: t.replace("{test_parent_directory}\\", "{test_parent_directory}/"),
    )


@pytest.fixture(autouse=True, scope="module")
def supress_copier_dependencies_debug_output():
    logging.getLogger("plumbum.local").setLevel("INFO")
    logging.getLogger("asyncio").setLevel("INFO")


@pytest.fixture(autouse=True)
def set_blessed_templates(mocker: MockerFixture):
    from algokit.cli.init import TemplateSource

    mocker.patch("algokit.cli.init._get_blessed_templates").return_value = {
        "simple": TemplateSource("gh:robdmoore/copier-helloworld"),
        "beaker": TemplateSource("gh:wilsonwaters/copier-testing-template"),
        "beaker_with_version": TemplateSource(
            "gh:wilsonwaters/copier-testing-template", "96fc7fd766fac607cdf5d69ee6e85ade04dddd47"
        ),
    }


def test_init_help():
    result = invoke("init -h")

    assert result.exit_code == 0
    verify(result.output)


def test_invalid_name():
    result = invoke("init --name invalid{name")

    assert result.exit_code != 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_no_interaction_required_no_git_no_network(tmp_path_factory: TempPathFactory):
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --UNSAFE-SECURITY-accept-template-url "
        + "--answer project_name test --answer greeting hi --answer include_extra_file yes",
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


def test_init_no_interaction_required_defaults_no_git_no_network(tmp_path_factory: TempPathFactory):
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' "
        + "--UNSAFE-SECURITY-accept-template-url --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path("myapp"),
        Path("myapp") / "hello_world",
        Path("myapp") / "hello_world" / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_minimal_interaction_required_no_git_no_network(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path("myapp"),
        Path("myapp") / "hello_world",
        Path("myapp") / "hello_world" / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_minimal_interaction_required_yes_git_no_network(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")
    dir_name = "myapp"
    result = invoke(
        f"init --name {dir_name} --git --template-url '{GIT_BUNDLE_PATH}' --defaults",
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
    assert paths == {Path(".git"), Path("hello_world")}
    git_rev_list = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"], cwd=created_dir, capture_output=True, text=True
    )
    assert git_rev_list.returncode == 0
    git_initial_commit_hash = git_rev_list.stdout[:7]
    verify(
        result.output,
        scrubber=make_output_scrubber(git_initial_commit_hash=git_initial_commit_hash),
    )


def test_init_do_not_use_existing_folder(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / "myapp").mkdir()
    mock_questionary_input.send_text("N")

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_use_existing_folder(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / "myapp").mkdir()
    mock_questionary_input.send_text("Y")  # override
    mock_questionary_input.send_text("Y")  # community warning

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_existing_filename_same_as_folder_name(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
):
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "myapp").touch()

    mock_questionary_input.send_text("Y")  # override
    mock_questionary_input.send_text("Y")  # community warning

    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_template_selection(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("\n")

    result = invoke(
        "init --name myapp --no-git --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_invalid_template_url(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")  # community warning
    result = invoke(
        "init --name myapp --no-git --template-url https://www.google.com --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_project_name(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")
    project_name = "FAKE_PROJECT"
    mock_questionary_input.send_text(project_name + "\n")
    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path(project_name),
        Path(project_name) / "hello_world",
        Path(project_name) / "hello_world" / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_project_name_not_empty(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")
    project_name = "FAKE_PROJECT"
    mock_questionary_input.send_text("\n")
    mock_questionary_input.send_text(project_name + "\n")
    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path(project_name),
        Path(project_name) / "hello_world",
        Path(project_name) / "hello_world" / "helloworld.txt",
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_project_name_reenter_folder_name(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")
    project_name = "FAKE_PROJECT"
    (cwd / project_name).mkdir()

    mock_questionary_input.send_text(project_name + "\n")
    mock_questionary_input.send_text("N")
    project_name_2 = "FAKE_PROJECT_2"
    mock_questionary_input.send_text(project_name_2 + "\n")
    mock_questionary_input.send_text("Y")
    result = invoke(
        f"init --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 0
    paths = {p.relative_to(cwd) for p in cwd.rglob("*")}
    assert paths == {
        Path(project_name_2),
        Path(project_name_2) / "hello_world",
        Path(project_name_2) / "hello_world" / "helloworld.txt",
        Path(project_name),
    }
    verify(result.output, scrubber=make_output_scrubber())


def test_init_ask_about_git(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")  # community one
    mock_questionary_input.send_text("Y")  # git
    dir_name = "myapp"
    result = invoke(
        f"init --name myapp --template-url '{GIT_BUNDLE_PATH}' --defaults",
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
    assert paths == {Path("hello_world"), Path(".git")}
    git_rev_list = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"], cwd=created_dir, capture_output=True, text=True
    )
    assert git_rev_list.returncode == 0
    git_initial_commit_hash = git_rev_list.stdout[:7]
    verify(
        result.output,
        scrubber=make_output_scrubber(git_initial_commit_hash=git_initial_commit_hash),
    )


def test_init_template_url_and_template_name(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("Y")  # community warning
    result = invoke(
        ("init --name myapp --no-git --template simple " f"--template-url '{GIT_BUNDLE_PATH}' --defaults"),
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_no_community_template(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    mock_questionary_input.send_text("N")  # community warning
    result = invoke(
        f"init --name myapp --no-git --template-url '{GIT_BUNDLE_PATH}' --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_init_input_template_url(tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput):
    cwd = tmp_path_factory.mktemp("cwd")

    # Source for special keys https://github.com/tmbo/questionary/blob/master/tests/prompts/test_select.py
    mock_questionary_input.send_text("\x1b[A")  # one up
    mock_questionary_input.send_text("\n")  # enter

    mock_questionary_input.send_text(str(GIT_BUNDLE_PATH) + "\n")  # name
    result = invoke(
        "init --name myapp --no-git --defaults",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_init_with_official_template_name(tmp_path_factory: TempPathFactory):
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "init --name myapp --no-git --template beaker --defaults -a run_poetry_install False",
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


def test_init_with_official_template_name_and_hash(tmp_path_factory: TempPathFactory):
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "init --name myapp --no-git --template beaker_with_version --defaults -a run_poetry_install False",
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


def test_init_with_env(tmp_path_factory: TempPathFactory):
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        (
            "init --name myapp --no-git --template beaker --defaults "
            '-a algod_token "abcdefghijklmnopqrstuvwxyz" -a algod_server http://mylocalserver -a algod_port 1234'
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
            Path("myapp") / "smart_contracts" / ".env.template",
        }
    )
    env_template_file_contents = (cwd / "myapp" / "smart_contracts" / ".env.template").read_text()

    verify(
        get_combined_verify_output(
            result.output, additional_name=".env.template", additional_output=env_template_file_contents
        ),
        scrubber=make_output_scrubber(),
    )
