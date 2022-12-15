import sys
from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


python_base_executable = str(Path(sys.executable).resolve())


@pytest.fixture(autouse=True)
def no_system_python_paths(mocker: MockerFixture):
    mocker.patch("algokit.core.bootstrap.which").return_value = None


def test_bootstrap_poetry_with_poetry(proc_mock: ProcMock):
    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_poetry_without_poetry(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry --version")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_poetry_without_poetry_failed_install(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_bad_exit_on("pipx install poetry")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output)


def test_bootstrap_poetry_without_poetry_failed_poetry_path(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("poetry install")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output)


def test_bootstrap_poetry_without_poetry_or_pipx_path(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("pipx --version")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))


def test_bootstrap_poetry_without_poetry_or_pipx_path_failed_install(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_bad_exit_on(f"{python_base_executable} -m pipx install poetry")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))


def test_bootstrap_poetry_without_poetry_or_pipx_path_failed_poetry_path(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_fail_on("poetry install")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))


def test_bootstrap_poetry_without_poetry_or_pipx_path_or_pipx_module(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry --version")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_bad_exit_on(f"{python_base_executable} -m pipx --version")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output.replace(python_base_executable, "{python_base_executable}"))
