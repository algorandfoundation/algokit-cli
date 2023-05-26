import pathlib
import shutil

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.core.typed_client_generation import TYPESCRIPT_NPX_PACKAGE, _snake_case
from approvaltests.namer import NamerFactory
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock
from tests.utils.which_mock import WhichMock


@pytest.fixture()
def application_json(tmp_path_factory: TempPathFactory) -> pathlib.Path:
    cwd = tmp_path_factory.mktemp("cwd")
    json_file = pathlib.Path(__file__).parent / "application.json"
    shutil.copy(json_file, cwd / "application.json")
    return cwd / "application.json"


@pytest.fixture(autouse=True)
def which_mock(mocker: MockerFixture) -> WhichMock:
    which_mock = WhichMock()
    which_mock.add("npx")
    mocker.patch("algokit.core.typed_client_generation.shutil.which").side_effect = which_mock.which
    return which_mock


def test_generate_help() -> None:
    result = invoke("generate -h")

    assert result.exit_code == 0
    verify(result.output)


def test_generate_no_options(application_json: pathlib.Path) -> None:
    result = invoke("generate client .", cwd=application_json.parent)
    assert result.exit_code != 0
    verify(result.output)


@pytest.mark.parametrize(
    ("options", "expected_output_path"),
    [
        ("-o client.py", "client.py"),
        ("--output {contract_name}.py", "hello_world_app.py"),
        ("-l python", "hello_world_app_client.py"),
        ("-o client.ts --language python", "client.ts"),
    ],
)
def test_generate_client_python(
    application_json: pathlib.Path, options: str, expected_output_path: pathlib.Path
) -> None:
    result = invoke(f"generate client {options} {application_json.name}", cwd=application_json.parent)

    assert result.exit_code == 0
    verify(result.output.replace("\\", "/"), options=NamerFactory.with_parameters(*options.split()))
    assert (application_json.parent / expected_output_path).exists()
    assert (application_json.parent / expected_output_path).read_text()


@pytest.mark.parametrize(
    ("options", "expected_output_path"),
    [
        ("-o client.ts", "client.ts"),
        ("--output {contract_name}.ts", "HelloWorldApp.ts"),
        ("-l typescript", "HelloWorldAppClient.ts"),
        ("-o client.py --language typescript", "client.py"),
    ],
)
def test_generate_client_typescript(
    proc_mock: ProcMock,
    application_json: pathlib.Path,
    options: str,
    expected_output_path: pathlib.Path,
) -> None:
    result = invoke(f"generate client {options} {application_json.name}", cwd=application_json.parent)
    assert result.exit_code == 0
    verify(result.output.replace("\\", "/"), options=NamerFactory.with_parameters(*options.split()))
    assert proc_mock.called == [
        f"/bin/npx --yes {TYPESCRIPT_NPX_PACKAGE} generate -a {application_json} -o {expected_output_path}".split()
    ]


def test_npx_missing(application_json: pathlib.Path, which_mock: WhichMock) -> None:
    which_mock.remove("npx")
    result = invoke(f"generate client -o client.ts {application_json.name}", cwd=application_json.parent)

    assert result.exit_code == 1
    verify(result.output)


def test_npx_failed(proc_mock: ProcMock, application_json: pathlib.Path) -> None:
    proc_mock.should_bad_exit_on(f"/bin/npx --yes {TYPESCRIPT_NPX_PACKAGE} generate -a {application_json} -o client.ts")
    result = invoke(f"generate client -o client.ts {application_json.name}", cwd=application_json.parent)

    assert result.exit_code == 1
    verify(result.output)


def test_snake_case() -> None:
    assert _snake_case("SnakeCase") == "snake_case"
    assert _snake_case("snakeCase") == "snake_case"
    assert _snake_case("snake-case") == "snake_case"
    assert _snake_case("snake_case") == "snake_case"
    assert _snake_case("SNAKE_CASE") == "snake_case"
    assert _snake_case("Snake_Case") == "snake_case"


# def test_format_client_name(application_json: pathlib.Path) -> None:
#
