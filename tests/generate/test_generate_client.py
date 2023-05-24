import pathlib
import shutil

import pytest
from _pytest.tmpdir import TempPathFactory

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def test_generate_help() -> None:
    result = invoke("generate -h")

    assert result.exit_code == 0
    verify(result.output)


@pytest.fixture()
def application_json(tmp_path_factory: TempPathFactory) -> pathlib.Path:
    cwd = tmp_path_factory.mktemp("cwd")
    json_file = pathlib.Path(__file__).parent / "application.json"
    shutil.copy(json_file, cwd / "application.json")
    return cwd / "application.json"


def test_generate_client_python(application_json: pathlib.Path) -> None:
    result = invoke(f"generate client -a {application_json} -o client.py")

    assert result.exit_code == 0
    verify(result.output)
    assert (application_json.parent / "client.py").exists()
    assert (application_json.parent / "client.py").read_text()


def test_generate_client_typescript(application_json: pathlib.Path) -> None:
    result = invoke(f"generate client -a {application_json} -o client.ts")

    assert result.exit_code == 0
    verify(result.output)
    assert (application_json.parent / "client.ts").exists()
    assert (application_json.parent / "client.ts").read_text()


def test_npm_installation_error(application_json: pathlib.Path) -> None:
    result = invoke(f"generate client -a {application_json} -o client.ts")

    assert result.exit_code == 1
    verify(result.output)
