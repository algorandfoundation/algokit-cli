import typing
from datetime import datetime
from pathlib import Path

import click
import pytest
from approvaltests.pytest.py_test_namer import PyTestNamer
from approvaltests.scrubbers.scrubbers import Scrubber
from pytest_mock import MockerFixture
from utils.approvals import TokenScrubber, combine_scrubbers, verify
from utils.click_invoker import invoke
from utils.proc_mock import ProcMock

PARENT_DIRECTORY = Path(__file__).parent


class VersionInfoType(typing.NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int


@pytest.fixture()
def mock_dependencies(request: pytest.FixtureRequest, mocker: MockerFixture) -> None:
    # Mock OS.platform
    platform_system: str = getattr(request, "param", "Darwin")

    mocker.patch("algokit.core.doctor.get_platform").return_value = f"{platform_system}-other-system-info"
    mocker.patch("algokit.cli.doctor.platform").system.return_value = platform_system
    # Mock datetime
    mocker.patch("algokit.core.doctor.datetime").now.return_value = datetime(1990, 12, 31, 10, 9, 8)
    # Mock shutil
    mocker.patch("algokit.core.doctor.which").side_effect = mock_shutil_which
    # Mock sys - Tuple[int, int, int, str, int]
    mocker.patch("algokit.core.doctor.sys_version", "3.6.2")
    mocker.patch("algokit.core.doctor.sys_executable", "{current_working_directory}/.venv/bin/python")


DOCKER_COMPOSE_VERSION_CMD = ["docker", "compose", "version", "--format", "json"]


@pytest.fixture(autouse=True)
def mock_happy_values(proc_mock: ProcMock) -> None:
    proc_mock.set_output(["pipx", "list", "--short"], ["aaa 2.3.4", "algokit 1.2.3", "copier 7.0.1"])
    proc_mock.set_output(
        ["pipx", "environment"],
        ["PIPX_SHARED_LIBS=/pipx/shared", "PIPX_LOCAL_VENVS=/pipx/venvs"],
    )
    proc_mock.set_output(["choco"], ["Chocolatey v0.10.15", "Please run 'choco -?' for help"])
    proc_mock.set_output(["brew", "-v"], ["Homebrew 3.6.15", "Homebrew/homebrew-core (blah)"])
    proc_mock.set_output(["docker", "-v"], ["Docker version 20.10.21, build baeda1f"])
    proc_mock.set_output(DOCKER_COMPOSE_VERSION_CMD, ['{"version": "v2.12.2"}'])
    proc_mock.set_output(["git", "--version"], ["git version 2.37.1 (Apple Git-137.1)"])
    proc_mock.set_output(["python", "--version"], ["Python 3.10.0"])
    proc_mock.set_output(["python3", "--version"], ["Python 3.11.0"])
    proc_mock.set_output(["pipx", "--version"], ["1.1.0"])
    proc_mock.set_output(["poetry", "--version"], ["blah blah", "", "Poetry (version 1.2.2)"])
    proc_mock.set_output(["node", "-v"], ["v18.12.1"])
    proc_mock.set_output(["npm", "-v"], ["8.19.2"])
    proc_mock.set_output(["npm.cmd", "-v"], ["8.19.2"])


def mock_shutil_which(python_command_name: str) -> str:
    if python_command_name == "python":
        return "/Library/Frameworks/Python.framework/Versions/3.10/bin/python"
    if python_command_name == "python3":
        return "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
    return ""


def make_output_scrubber(**extra_tokens: str) -> Scrubber:
    default_tokens = {"test_parent_directory": str(PARENT_DIRECTORY)}
    tokens = default_tokens | extra_tokens
    return combine_scrubbers(
        click.unstyle,
        TokenScrubber(tokens=tokens),
        TokenScrubber(tokens={"test_parent_directory": str(PARENT_DIRECTORY).replace("\\", "/")}),
        lambda t: t.replace("{test_parent_directory}\\", "{test_parent_directory}/"),
    )


def test_doctor_help(mocker: MockerFixture, mock_dependencies: None):
    result = invoke("doctor -h")

    assert result.exit_code == 0
    verify(result.output)


def test_doctor_with_copy(mocker: MockerFixture, mock_dependencies: None):
    # Mock pyclip
    mocked_os = mocker.patch("algokit.cli.doctor.pyclip.copy")
    result = invoke("doctor -c")

    assert result.exit_code == 0
    mocked_os.assert_called_once()
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.parametrize(
    "mock_dependencies",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["mock_dependencies"],
)
def test_doctor_successful(request: pytest.FixtureRequest, mock_dependencies: None):
    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber(), namer=PyTestNamer(request))


def test_doctor_with_docker_compose_warning(proc_mock: ProcMock, mock_dependencies: None):
    proc_mock.set_output(DOCKER_COMPOSE_VERSION_CMD, ['{"version": "v2.1.3"}'])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_with_git_warning_on_mac(mocker: MockerFixture, proc_mock: ProcMock, mock_dependencies: None):
    proc_mock.set_output(["git", "--version"], ["EMPTY"])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.parametrize("mock_dependencies", [pytest.param("Windows", id="windows")], indirect=["mock_dependencies"])
def test_doctor_with_git_warning_on_windows(mocker: MockerFixture, proc_mock: ProcMock, mock_dependencies: None):
    proc_mock.set_output(["git", "--version"], [])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.parametrize(
    "mock_dependencies",
    [
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ],
    indirect=["mock_dependencies"],
)
def test_doctor_all_failed(
    request: pytest.FixtureRequest, mocker: MockerFixture, proc_mock: ProcMock, mock_dependencies: None
):

    mocker.patch("algokit.core.doctor.sys_executable", "")

    proc_mock.set_output(["pipx", "list", "--short"], [])
    proc_mock.set_output(["pipx", "environment"], [])
    proc_mock.set_output(["choco"], [])
    proc_mock.set_output(["brew", "-v"], [])
    proc_mock.set_output(["docker", "-v"], [])
    proc_mock.set_output(DOCKER_COMPOSE_VERSION_CMD, ["{}"])
    proc_mock.set_output(["git", "--version"], [])
    proc_mock.set_output(["python", "--version"], [])
    proc_mock.set_output(["python3", "--version"], [])
    proc_mock.set_output(["pipx", "--version"], [])
    proc_mock.set_output(["poetry", "--version"], [])
    proc_mock.set_output(["node", "-v"], [])
    proc_mock.set_output(["npm", "-v"], [])
    proc_mock.set_output(["npm.cmd", "-v"], [])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber(), namer=PyTestNamer(request))


def test_doctor_with_weird_values_on_mac(mocker: MockerFixture, proc_mock: ProcMock, mock_dependencies: None):
    proc_mock.set_output(["brew", "-v"], ["Homebrew 3.6.15-31-g82d89bb"])

    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.parametrize("mock_dependencies", [pytest.param("Windows", id="windows")], indirect=["mock_dependencies"])
def test_doctor_with_weird_values_on_windows(mocker: MockerFixture, proc_mock: ProcMock, mock_dependencies: None):
    proc_mock.set_output(["git", "--version"], ["git version 2.31.0.windows.1"])
    proc_mock.set_output(
        ["choco"], ["Chocolatey v0.10.15", "choco: Please run 'choco -?' or 'choco <command> -?' for help menu."]
    )
    proc_mock.set_output(["npm.cmd", "-v"], [" 16.17.0 "])

    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())
