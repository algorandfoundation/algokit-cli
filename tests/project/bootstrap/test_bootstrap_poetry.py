import sys
from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import FixtureRequest
from approvaltests.pytest.py_test_namer import PyTestNamer
from prompt_toolkit.input import PipeInput
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


@pytest.fixture(scope="module")
def python_base_executable() -> str:
    from algokit.core.utils import get_base_python_path

    value = get_base_python_path()
    if value is None:
        pytest.fail("Python base detection failed, this should work (even in CI)")
    return value


@pytest.fixture
def system_python_paths(request: FixtureRequest, mocker: MockerFixture) -> MagicMock:
    python_names: list[str] = getattr(request, "param", [])

    def which(cmd: str) -> str | None:
        if cmd in python_names:
            return f"/bin/{cmd}"
        return None

    mock = mocker.patch("algokit.core.utils.which")
    mock.side_effect = which
    return mock


@pytest.fixture(autouse=True)
def uvx_which_mock(mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.utils.shutil.which", side_effect=lambda cmd: "/bin/uvx" if cmd == "uvx" else None)


def test_base_python_path(python_base_executable: str) -> None:
    """When running in a venv (expected test mode), we should be able to resolve to base python.
    Otherwise, they should be the same"""
    assert (python_base_executable == sys.executable) == (sys.prefix == sys.base_prefix)


@pytest.mark.usefixtures("proc_mock")
def test_bootstrap_poetry_with_poetry() -> None:
    result = invoke("project bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_poetry_without_poetry(proc_mock: ProcMock, mock_questionary_input: PipeInput) -> None:
    proc_mock.should_fail_on("poetry --version")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("project bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_poetry_without_poetry_failed_install(proc_mock: ProcMock, mock_questionary_input: PipeInput) -> None:
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_bad_exit_on("uv tool install poetry")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("project bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output)


def test_bootstrap_poetry_without_poetry_failed_poetry_path(
    proc_mock: ProcMock, mock_questionary_input: PipeInput
) -> None:
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("poetry install")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("project bootstrap poetry")

    assert result.exit_code == 0
    assert any(call.command == ["uvx", "--from=poetry", "poetry", "install"] for call in proc_mock.called)


@pytest.mark.parametrize(
    "system_python_paths",
    [
        pytest.param([], id="no_system_pythons"),
        pytest.param(["python"], id="python_only"),
        pytest.param(["python3"], id="python3_only"),
        pytest.param(["python", "python3"], id="python_and_python3"),
    ],
    indirect=["system_python_paths"],
)
@pytest.mark.usefixtures("system_python_paths")
def test_bootstrap_poetry_without_poetry_or_pipx_path(
    request: FixtureRequest,
    proc_mock: ProcMock,
    python_base_executable: str,
    mock_questionary_input: PipeInput,
) -> None:
    proc_mock.should_fail_on("poetry --version")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("project bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output.replace(python_base_executable, "{python_base_executable}"), namer=PyTestNamer(request))


@pytest.mark.usefixtures("system_python_paths")
def test_bootstrap_poetry_without_poetry_or_pipx_path_failed_install(
    proc_mock: ProcMock, python_base_executable: str, mock_questionary_input: PipeInput
) -> None:
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_bad_exit_on("uv tool install poetry")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("project bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))


@pytest.mark.usefixtures("system_python_paths")
def test_bootstrap_poetry_without_poetry_or_pipx_path_failed_poetry_path(
    proc_mock: ProcMock, mock_questionary_input: PipeInput
) -> None:
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("poetry install")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("project bootstrap poetry")

    assert result.exit_code == 0
    assert any(call.command == ["uvx", "--from=poetry", "poetry", "install"] for call in proc_mock.called)


@pytest.mark.usefixtures("system_python_paths")
def test_bootstrap_poetry_without_poetry_or_pipx_path_or_pipx_module(
    proc_mock: ProcMock,
    python_base_executable: str,
    mock_questionary_input: PipeInput,
    mocker: MockerFixture,
) -> None:
    proc_mock.should_fail_on("poetry --version")
    mocker.patch("algokit.core.utils.shutil.which", return_value=None)
    mocker.patch("algokit.core.utils._get_candidate_pipx_commands", return_value=[])
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("project bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))


def test_bootstrap_poetry_without_poetry_with_uv_no_uvx_uses_runner_fallback(
    proc_mock: ProcMock, mock_questionary_input: PipeInput, mocker: MockerFixture
) -> None:
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("poetry install")
    mocker.patch("algokit.core.utils.shutil.which", side_effect=lambda cmd: "/bin/uv" if cmd == "uv" else None)
    mock_questionary_input.send_text("Y")

    result = invoke("project bootstrap poetry")

    assert result.exit_code == 0
    assert any(call.command == ["uv", "tool", "run", "--from=poetry", "poetry", "install"] for call in proc_mock.called)
