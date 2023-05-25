import pathlib
import shutil

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.cli.generate import format_client_name, snake_case

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.fixture()
def application_json(tmp_path_factory: TempPathFactory) -> pathlib.Path:
    cwd = tmp_path_factory.mktemp("cwd")
    json_file = pathlib.Path(__file__).parent / "application.json"
    shutil.copy(json_file, cwd / "application.json")
    return cwd / "application.json"


def test_generate_help() -> None:
    result = invoke("generate -h")

    assert result.exit_code == 0
    verify(result.output)


def test_generate_client_python(application_json: pathlib.Path) -> None:
    result = invoke(f"generate client -a {application_json.name} -o client.py", cwd=application_json.parent)

    assert result.exit_code == 0
    verify(result.output)
    assert (application_json.parent / "client.py").exists()
    assert (application_json.parent / "client.py").read_text()


def test_generate_client_typescript(application_json: pathlib.Path) -> None:
    result = invoke(f"generate client -a {application_json.name} -o client.ts", cwd=application_json.parent)

    assert result.exit_code == 0
    verify(result.output.replace("npx.cmd", "npx"))
    assert (application_json.parent / "client.ts").exists()
    assert (application_json.parent / "client.ts").read_text()


def test_npx_missing(proc_mock: ProcMock, application_json: pathlib.Path) -> None:
    proc_mock.should_fail_on(
        f"npx --yes @algorandfoundation/algokit-client-generator@v2.0.0-beta.1 generate -a {application_json} "
        f"-o {application_json.parent / 'client.ts'}"
    )
    proc_mock.should_fail_on(
        f"npx.cmd --yes @algorandfoundation/algokit-client-generator@v2.0.0-beta.1 generate -a {application_json} "
        f"-o {application_json.parent / 'client.ts'}"
    )
    result = invoke(f"generate client -a {application_json.name} -o client.ts", cwd=application_json.parent)

    assert result.exit_code == 1
    verify(result.output.replace("npx.cmd", "npx"))


def test_npx_failed(proc_mock: ProcMock, application_json: pathlib.Path) -> None:
    proc_mock.should_bad_exit_on(
        f"npx --yes @algorandfoundation/algokit-client-generator@v2.0.0-beta.1 generate -a {application_json} "
        f"-o {application_json.parent / 'client.ts'}"
    )
    proc_mock.should_bad_exit_on(
        f"npx.cmd --yes @algorandfoundation/algokit-client-generator@v2.0.0-beta.1 generate -a {application_json} "
        f"-o {application_json.parent / 'client.ts'}"
    )
    result = invoke(f"generate client -a {application_json.name} -o client.ts", cwd=application_json.parent)

    assert result.exit_code == 1
    verify(result.output.replace("npx.cmd", "npx"))


def test_snake_case() -> None:
    assert snake_case("SnakeCase") == "snake_case"
    assert snake_case("snakeCase") == "snake_case"
    assert snake_case("snake-case") == "snake_case"
    assert snake_case("snake_case") == "snake_case"
    assert snake_case("SNAKE_CASE") == "snake_case"
    assert snake_case("Snake_Case") == "snake_case"


def test_format_client_name(application_json: pathlib.Path) -> None:
    output = pathlib.Path("./output/%name%.txt")
    result = format_client_name(output=output, application_file=application_json)
    result_str = str(result).replace("\\", "/")
    assert result_str == "output/hello_world_app.txt"

    output = pathlib.Path("./output/%parent_dir%.txt")
    result = format_client_name(output=output, application_file=application_json)
    result_str = str(result).replace("\\", "/")
    assert result_str == f"output/{application_json.parent.name}.txt"
