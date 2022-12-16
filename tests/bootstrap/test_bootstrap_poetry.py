import logging
import sys
from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import FixtureRequest
from approvaltests.pytest.py_test_namer import PyTestNamer
from prompt_toolkit.input import PipeInput
from pytest_mock import MockerFixture
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


@pytest.fixture(scope="module")
def python_base_executable() -> str:
    from algokit.core.bootstrap import _get_base_python_path

    value = _get_base_python_path()
    if value is None:
        pytest.fail("Python base detection failed, this should work (even in CI)")
    return value


@pytest.fixture(autouse=True, scope="module")
def supress_questionary_dependencies_debug_output():
    logging.getLogger("asyncio").setLevel("INFO")


@pytest.fixture()
def system_python_paths(request: FixtureRequest, mocker: MockerFixture) -> MagicMock:
    python_names: list[str] = getattr(request, "param", [])

    def which(cmd: str) -> str | None:
        if cmd in python_names:
            return f"/bin/{cmd}"
        return None

    mock = mocker.patch("algokit.core.bootstrap.which")
    mock.side_effect = which
    return mock


def test_base_python_path(python_base_executable: str):
    """When running in a venv (expected test mode), we should be able to resolve to base python.
    Otherwise, they should be the same"""
    assert (python_base_executable == sys.executable) == (sys.prefix == sys.base_prefix)


def test_bootstrap_poetry_with_poetry(proc_mock: ProcMock):
    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_poetry_without_poetry(proc_mock: ProcMock, mock_questionary_input: PipeInput):
    proc_mock.should_fail_on("poetry --version")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_poetry_without_poetry_failed_install(proc_mock: ProcMock, mock_questionary_input: PipeInput):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_bad_exit_on("pipx install poetry")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output)


def test_bootstrap_poetry_without_poetry_failed_poetry_path(proc_mock: ProcMock, mock_questionary_input: PipeInput):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("poetry install")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output)


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
def test_bootstrap_poetry_without_poetry_or_pipx_path(
    request: FixtureRequest,
    proc_mock: ProcMock,
    system_python_paths: MagicMock,
    python_base_executable: str,
    mock_questionary_input: PipeInput,
):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("pipx --version")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output.replace(python_base_executable, "{python_base_executable}"), namer=PyTestNamer(request))


def test_bootstrap_poetry_without_poetry_or_pipx_path_failed_install(
    proc_mock: ProcMock, system_python_paths: MagicMock, python_base_executable: str, mock_questionary_input: PipeInput
):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_bad_exit_on(f"{python_base_executable} -m pipx install poetry")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))


def test_bootstrap_poetry_without_poetry_or_pipx_path_failed_poetry_path(
    proc_mock: ProcMock, system_python_paths: MagicMock, python_base_executable: str, mock_questionary_input: PipeInput
):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_fail_on("poetry install")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))


def test_bootstrap_poetry_without_poetry_or_pipx_path_or_pipx_module(
    proc_mock: ProcMock, system_python_paths: MagicMock, python_base_executable: str, mock_questionary_input: PipeInput
):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_bad_exit_on(f"{python_base_executable} -m pipx --version")
    # Yes, install poetry
    mock_questionary_input.send_text("Y")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))
