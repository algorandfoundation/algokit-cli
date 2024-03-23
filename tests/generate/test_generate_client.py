import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.core.typed_client_generation import (
    PYTHON_PYPI_PACKAGE,
    TYPESCRIPT_NPX_PACKAGE,
    _snake_case,
)
from algokit.core.utils import is_windows
from approvaltests.namer import NamerFactory
from approvaltests.pytest.py_test_namer import PyTestNamer
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock
from tests.utils.which_mock import WhichMock

DirWithAppSpecFactory = Callable[[Path, str], Path]
DEFAULT_TYPESCRIPT_NPX_PACKAGE_VERSION = "latest"


def _normalize_output(output: str) -> str:
    return output.replace("\\", "/").replace(TYPESCRIPT_NPX_PACKAGE, "{typed_client_package}")


def _get_npx_command() -> str:
    return "npx" if not is_windows() else "npx.cmd"


def _get_python_generate_command(version: str | None, application_json: Path, expected_output_path: Path) -> str:
    return (
        f"pipx run --spec={PYTHON_PYPI_PACKAGE}{f'=={version}' if version is not None else ''} "
        f"algokitgen-py -a {application_json} -o {expected_output_path}"
    )


def _get_typescript_generate_command(version: str | None, application_json: Path, expected_output_path: Path) -> str:
    return (
        f"{_get_npx_command()} --yes {TYPESCRIPT_NPX_PACKAGE}{f'@{version}' if version is not None else ''} "
        f"generate -a {application_json} -o {expected_output_path}"
    )


@pytest.fixture()
def cwd(tmp_path_factory: TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("cwd")


@pytest.fixture()
def dir_with_app_spec_factory() -> DirWithAppSpecFactory:
    app_spec_example_path = Path(__file__).parent / "application.json"

    def factory(app_spec_dir: Path, app_spec_file_name: str) -> Path:
        app_spec_dir.mkdir(exist_ok=True, parents=True)
        app_spec_path = app_spec_dir / app_spec_file_name
        shutil.copy(app_spec_example_path, app_spec_path)
        return app_spec_path

    return factory


@pytest.fixture()
def application_json(cwd: Path, dir_with_app_spec_factory: DirWithAppSpecFactory) -> Path:
    return dir_with_app_spec_factory(cwd, "application.json")


@pytest.fixture()
def arc32_json(cwd: Path, dir_with_app_spec_factory: DirWithAppSpecFactory) -> Path:
    return dir_with_app_spec_factory(cwd, "app.arc32.json")


@pytest.fixture(autouse=True)
def which_mock(mocker: MockerFixture) -> WhichMock:
    which_mock = WhichMock()
    which_mock.add("npx")
    which_mock.add("npm")
    which_mock.add("pipx")
    mocker.patch("algokit.core.typed_client_generation.shutil.which").side_effect = which_mock.which
    return which_mock


def test_generate_help() -> None:
    result = invoke("generate -h")

    assert result.exit_code == 0
    verify(result.output)


def test_generate_no_options(application_json: Path) -> None:
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
        ("-o client.py --language python --version 1.1.2", "client.py"),
        ("-l python -v 1.1.0", "hello_world_app_client.py"),
    ],
)
def test_generate_client_python(
    proc_mock: ProcMock,
    application_json: Path,
    options: str,
    expected_output_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    result = invoke(f"generate client {options} {application_json.name}", cwd=application_json.parent)

    assert result.exit_code == 0
    verify(
        _normalize_output(result.output),
        namer=PyTestNamer(request),
        options=NamerFactory.with_parameters(*options.split()),
    )
    if "--version" in options or "-v" in options:
        version = options.split()[-1]
    else:
        version = None
    assert len(proc_mock.called) == 3  # noqa: PLR2004
    assert (
        proc_mock.called[2].command
        == _get_python_generate_command(version, application_json, expected_output_path).split()
    )


@pytest.mark.usefixtures("proc_mock")
def test_pipx_missing(application_json: Path, mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.utils.get_candidate_pipx_commands", return_value=[])
    result = invoke(f"generate client -o client.py -l python {application_json.name}", cwd=application_json.parent)

    assert result.exit_code == 1
    verify(_normalize_output(result.output))


@pytest.mark.parametrize(
    ("options", "expected_output_path"),
    [
        ("-o client.py", "client.py"),
    ],
)
def test_generate_client_python_arc32_filename(
    proc_mock: ProcMock, arc32_json: Path, options: str, expected_output_path: Path
) -> None:
    result = invoke(f"generate client {options} {arc32_json.name}", cwd=arc32_json.parent)

    assert result.exit_code == 0
    verify(_normalize_output(result.output), options=NamerFactory.with_parameters(*options.split()))

    assert len(proc_mock.called) == 3  # noqa: PLR2004
    assert proc_mock.called[2].command == _get_python_generate_command(None, arc32_json, expected_output_path).split()


@pytest.mark.usefixtures("mock_platform_system")
@pytest.mark.parametrize(
    ("options", "expected_output_path"),
    [
        ("-o client.ts", "client.ts"),
        ("--output {contract_name}.ts", "HelloWorldApp.ts"),
        ("-l typescript", "HelloWorldAppClient.ts"),
        ("-o client.py --language typescript", "client.py"),
        ("-o client.ts --language typescript --version 3.0.0", "client.ts"),
        ("-l typescript -v 2.6.0", "HelloWorldAppClient.ts"),
    ],
)
def test_generate_client_typescript(
    proc_mock: ProcMock,
    application_json: Path,
    options: str,
    expected_output_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    result = invoke(f"generate client {options} {application_json.name}", cwd=application_json.parent)
    assert result.exit_code == 0
    verify(
        _normalize_output(result.output),
        namer=PyTestNamer(request),
        options=NamerFactory.with_parameters(*options.split()),
    )
    if "--version" in options or "-v" in options:
        version = options.split()[-1]
    else:
        version = "latest"
    assert len(proc_mock.called) == 2  # noqa: PLR2004
    assert (
        proc_mock.called[1].command
        == _get_typescript_generate_command(version, application_json, expected_output_path).split()
    )


@pytest.mark.usefixtures("proc_mock")
def test_npx_missing(application_json: Path, which_mock: WhichMock) -> None:
    which_mock.remove("npx")
    result = invoke(f"generate client -o client.ts {application_json.name}", cwd=application_json.parent)

    assert result.exit_code == 1
    verify(_normalize_output(result.output))


@pytest.mark.usefixtures("mock_platform_system")
def test_npx_failed(
    proc_mock: ProcMock,
    application_json: Path,
    request: pytest.FixtureRequest,
) -> None:
    proc_mock.should_bad_exit_on(_get_typescript_generate_command("latest", application_json, Path("client.ts")))
    result = invoke(f"generate client -o client.ts {application_json.name}", cwd=application_json.parent)

    assert result.exit_code == -1
    verify(
        _normalize_output(result.output),
        namer=PyTestNamer(request),
    )


def test_generate_client_recursive(
    proc_mock: ProcMock, cwd: Path, dir_with_app_spec_factory: DirWithAppSpecFactory
) -> None:
    dir_paths = [
        cwd / "dir1",
        cwd / "dir2",
        cwd / "dir2" / "sub_dir",
    ]
    for dir_path in dir_paths:
        dir_with_app_spec_factory(dir_path, "application.json")

    result = invoke("generate client -o {app_spec_dir}/output.py .", cwd=cwd)
    assert result.exit_code == 0
    verify(_normalize_output(result.output))

    for index, dir_path in enumerate(dir_paths):
        output_path = dir_path / "output.py"
        proc_mock.called[index].command[-1] = str(output_path)


@pytest.mark.usefixtures("proc_mock")
def test_generate_client_no_app_spec_found(cwd: Path) -> None:
    result = invoke("generate client -o output.py .", cwd=cwd)
    assert result.exit_code == 1
    verify(_normalize_output(result.output))


@pytest.mark.usefixtures("proc_mock")
def test_generate_client_output_path_is_dir(application_json: Path) -> None:
    cwd = application_json.parent
    (cwd / "hello_world_app.py").mkdir()

    result = invoke("generate client -o {contract_name}.py .", cwd=cwd)
    assert result.exit_code == 0
    verify(_normalize_output(result.output))


def test_snake_case() -> None:
    assert _snake_case("SnakeCase") == "snake_case"
    assert _snake_case("snakeCase") == "snake_case"
    assert _snake_case("snake-case") == "snake_case"
    assert _snake_case("snake_case") == "snake_case"
    assert _snake_case("SNAKE_CASE") == "snake_case"
    assert _snake_case("Snake_Case") == "snake_case"
