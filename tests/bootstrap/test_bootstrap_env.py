from _pytest.tmpdir import TempPathFactory
from utils.approvals import verify
from utils.click_invoker import invoke

from tests import get_combined_verify_output


def test_bootstrap_env_no_files(tmp_path_factory: TempPathFactory):
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "bootstrap env",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_env_dotenv_exists(tmp_path_factory: TempPathFactory):
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env").touch()

    result = invoke(
        "bootstrap env",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_env_dotenv_missing_template_exists(tmp_path_factory: TempPathFactory):
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env.template").write_text("env_template_contents")

    result = invoke(
        "bootstrap env",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(get_combined_verify_output(result.output, ".env", (cwd / ".env").read_text("utf-8")))
