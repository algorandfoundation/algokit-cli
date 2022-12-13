import sys

from pytest_mock import MockerFixture
from utils.approvals import verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock


def test_bootstrap_poetry_with_poetry(proc_mock: ProcMock):
    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_poetry_without_poetry(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry -V")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_poetry_without_poetry_failed_install(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry -V")
    proc_mock.should_bad_exit_on("pipx install poetry")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output)


def test_bootstrap_poetry_without_poetry_failed_poetry_path(proc_mock: ProcMock):
    proc_mock.should_fail_on("poetry -V")
    proc_mock.should_fail_on("poetry install")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(result.output)


def test_bootstrap_poetry_without_poetry_or_pipx_path_linux(proc_mock: ProcMock, mocker: MockerFixture):
    mocker.patch("algokit.cli.bootstrap.system").return_value = "Linux"
    proc_mock.should_fail_on("poetry -V")
    proc_mock.should_fail_on("pipx --version")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(
        result.output.replace(sys.base_prefix, "{python_base_path}").replace(
            "{python_base_path}\\bin\\", "{python_base_path}/bin/"
        )
    )


def test_bootstrap_poetry_without_poetry_or_pipx_path_windows(proc_mock: ProcMock, mocker: MockerFixture):
    mocker.patch("algokit.cli.bootstrap.system").return_value = "Windows"
    proc_mock.should_fail_on("poetry -V")
    proc_mock.should_fail_on("pipx --version")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 0
    verify(
        result.output.replace(sys.base_prefix, "{python_base_path}").replace(
            "{python_base_path}/Scripts/", "{python_base_path}\\Scripts\\"
        )
    )


def test_bootstrap_poetry_without_poetry_or_pipx_path_failed_install(proc_mock: ProcMock, mocker: MockerFixture):
    mocker.patch("algokit.cli.bootstrap.system").return_value = "Linux"
    proc_mock.should_fail_on("poetry -V")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_bad_exit_on(f"{sys.base_prefix}/bin/python3 -m pipx install poetry")
    proc_mock.should_bad_exit_on(f"{sys.base_prefix}\\bin\\python3 -m pipx install poetry")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(
        result.output.replace(sys.base_prefix, "{python_base_path}").replace(
            "{python_base_path}\\bin\\", "{python_base_path}/bin/"
        )
    )


def test_bootstrap_poetry_without_poetry_or_pipx_path_failed_poetry_path(proc_mock: ProcMock, mocker: MockerFixture):
    mocker.patch("algokit.cli.bootstrap.system").return_value = "Linux"
    proc_mock.should_fail_on("poetry -V")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_fail_on("poetry install")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(
        result.output.replace(sys.base_prefix, "{python_base_path}").replace(
            "{python_base_path}\\bin\\", "{python_base_path}/bin/"
        )
    )


def test_bootstrap_poetry_without_poetry_or_pipx_path_or_pipx_module(proc_mock: ProcMock, mocker: MockerFixture):
    mocker.patch("algokit.cli.bootstrap.system").return_value = "Linux"
    proc_mock.should_fail_on("poetry -V")
    proc_mock.should_fail_on("pipx --version")
    proc_mock.should_bad_exit_on(f"{sys.base_prefix}/bin/python3 -m pipx --version")
    proc_mock.should_bad_exit_on(f"{sys.base_prefix}\\bin\\python3 -m pipx --version")

    result = invoke("bootstrap poetry")

    assert result.exit_code == 1
    verify(
        result.output.replace(sys.base_prefix, "{python_base_path}").replace(
            "{python_base_path}\\bin\\", "{python_base_path}/bin/"
        )
    )
