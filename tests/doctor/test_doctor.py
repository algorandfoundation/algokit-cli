import typing
from datetime import datetime
from pathlib import Path

import click
import pytest
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


@pytest.fixture(autouse=True)
def mock_dependencies(mocker: MockerFixture) -> None:
    # Mock OS.platform
    mocked_os = mocker.patch("algokit.cli.doctor.platform")
    mocked_os.system.return_value = "darwin"
    # Mock platform
    mocked_os = mocker.patch("algokit.core.doctor.platform")
    mocked_os.win32_ver.return_value = ("windows_version", "", "", "")
    mocked_os.mac_ver.return_value = ("mac_os_version", "", "", "")
    mocked_os.version.return_value = "linux_version"
    # Mock datetime
    mocked_date = mocker.patch("algokit.core.doctor.datetime")
    mocked_date.now.return_value = datetime(1990, 12, 31, 10, 9, 8)
    # Mock shutil
    mocked_shutil = mocker.patch("algokit.core.doctor.shutil")
    mocked_shutil.which.return_value = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
    # Mock sys - Tuple[int, int, int, str, int]
    mocker.patch("algokit.core.doctor.sys_version_info", VersionInfoType(3, 6, 2, "blah", 0))
    mocker.patch("algokit.core.doctor.sys_executable", "{current_working_directory}/.venv/bin/python")


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
    proc_mock.set_output(["docker-compose", "-v"], ["Docker Compose version v2.12.2"])
    proc_mock.set_output(["git", "--version"], ["git version 2.37.1 (Apple Git-137.1)"])
    proc_mock.set_output(["python3", "--version"], ["Python 3.11.0"])
    proc_mock.set_output(["pipx", "--version"], ["1.1.0"])
    proc_mock.set_output(["poetry", "--version"], ["blah blah", "", "Poetry (version 1.2.2)"])
    proc_mock.set_output(["node", "-v"], ["v18.12.1"])
    proc_mock.set_output(["npm", "-v"], ["8.19.2"])


def make_output_scrubber(**extra_tokens: str) -> Scrubber:
    default_tokens = {"test_parent_directory": str(PARENT_DIRECTORY)}
    tokens = default_tokens | extra_tokens
    return combine_scrubbers(
        click.unstyle,
        TokenScrubber(tokens=tokens),
        TokenScrubber(tokens={"test_parent_directory": str(PARENT_DIRECTORY).replace("\\", "/")}),
        lambda t: t.replace("{test_parent_directory}\\", "{test_parent_directory}/"),
    )


def test_doctor_help(mocker: MockerFixture):
    result = invoke("doctor -h")

    assert result.exit_code == 0
    verify(result.output)


def test_doctor_with_copy(mocker: MockerFixture):
    # Mock pyclip
    mocked_os = mocker.patch("algokit.cli.doctor.pyclip.copy")
    result = invoke("doctor -c")

    assert result.exit_code == 0
    mocked_os.assert_called_once()
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_successful_on_mac():
    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_successful_on_windows(mocker: MockerFixture, proc_mock: ProcMock):
    mocked_os = mocker.patch("algokit.cli.doctor.platform")
    mocked_os.system.return_value = "windows"
    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_successful_on_linux(mocker: MockerFixture, proc_mock: ProcMock):
    mocked_os = mocker.patch("algokit.cli.doctor.platform")
    mocked_os.system.return_value = "linux"
    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_with_docker_compose_warning(proc_mock: ProcMock):
    proc_mock.set_output(["docker-compose", "-v"], ["Docker Compose version v2.1.3"])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_with_git_warning_on_mac(mocker: MockerFixture, proc_mock: ProcMock):
    proc_mock.set_output(["git", "--version"], ["EMPTY"])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_with_git_warning_on_windows(mocker: MockerFixture, proc_mock: ProcMock):
    mocked_os = mocker.patch("algokit.cli.doctor.platform")
    mocked_os.system.return_value = "windows"

    proc_mock.set_output(["git", "--version"], [])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_all_failed_on_mac(mocker: MockerFixture, proc_mock: ProcMock):
    proc_mock.set_output(["pipx", "list", "--short"], [])
    proc_mock.set_output(["pipx", "environment"], [])
    proc_mock.set_output(["choco"], [])
    proc_mock.set_output(["brew", "-v"], [])
    proc_mock.set_output(["docker", "-v"], [])
    proc_mock.set_output(["docker-compose", "-v"], [])
    proc_mock.set_output(["git", "--version"], [])
    proc_mock.set_output(["python3", "--version"], [])
    proc_mock.set_output(["pipx", "--version"], [])
    proc_mock.set_output(["poetry", "--version"], [])
    proc_mock.set_output(["node", "-v"], [])
    proc_mock.set_output(["npm", "-v"], [])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_with_weird_values_on_mac(mocker: MockerFixture, proc_mock: ProcMock):
    proc_mock.set_output(["brew", "-v"], ["Homebrew 3.6.15-31-g82d89bb"])

    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())

