import pathlib
import shutil

from _pytest.tmpdir import TempPathFactory

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def test_generate_help() -> None:
    result = invoke("generate -h")

    assert result.exit_code == 0
    verify(result.output)


def test_generate_client_python(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    json_file = pathlib.Path(__file__).parent / "application.json"
    shutil.copy(json_file, cwd / "application.json")
    result = invoke("generate client -a application.json -o client.py", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)
    assert (cwd / "client.py").exists()
    assert (cwd / "client.py").read_text()


def test_generate_client_typescript(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    json_file = pathlib.Path(__file__).parent / "application.json"
    shutil.copy(json_file, cwd / "application.json")
    result = invoke("generate client -a application.json -o client.ts", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)
    assert (cwd / "client.ts").exists()
    assert (cwd / "client.ts").read_text()


def test_npm_installation_error(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    json_file = pathlib.Path(__file__).parent / "application.json"
    shutil.copy(json_file, cwd / "application.json")
    result = invoke("generate client -a application.json -o client.ts", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)
