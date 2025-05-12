import typing
from datetime import datetime
from pathlib import Path

import click
import pytest
from approvaltests.pytest.py_test_namer import PyTestNamer
from approvaltests.scrubbers.scrubbers import Scrubber
from pytest_mock import MockerFixture

from tests.utils.approvals import TokenScrubber, combine_scrubbers, verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock

PARENT_DIRECTORY = Path(__file__).parent

DOCKER_COMPOSE_VERSION_COMMAND = ["docker", "compose", "version", "--format", "json"]


class VersionInfoType(typing.NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int


@pytest.fixture
def _mock_doctor_dependencies(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.doctor.get_current_package_version").return_value = "1.2.3"
    mocker.patch("algokit.cli.doctor.get_latest_github_version").return_value = "1.2.3"
    # Mock datetime
    mocker.patch("algokit.cli.doctor.dt").datetime.now.side_effect = lambda _, tz=None: datetime(
        1990, 12, 31, 10, 9, 8, tzinfo=tz
    )
    # Mock shutil
    mocker.patch("algokit.core.doctor.which").side_effect = mock_shutil_which
    # Mock sys - Tuple[int, int, int, str, int]
    sys_module = mocker.patch("algokit.cli.doctor.sys")
    sys_module.version = "3.6.2"
    sys_module.prefix = "/home/me/.local/pipx/venvs/algokit"
    # Mock enable binary mode to ignore outputting package information to
    # simplify snapshot diffs - otherwise each new run may fail whenever main prod
    # dependencies are updated
    mocker.patch("algokit.cli.doctor.is_binary_mode").return_value = True


@pytest.fixture(autouse=True)
def _mock_happy_values(proc_mock: ProcMock) -> None:
    proc_mock.set_output(["winget", "--version"], ["v1.8.1911"])
    proc_mock.set_output(["brew", "--version"], ["Homebrew 3.6.15", "Homebrew/homebrew-core (blah)"])
    proc_mock.set_output(["docker", "--version"], ["Docker version 20.10.21, build baeda1f"])
    proc_mock.set_output(DOCKER_COMPOSE_VERSION_COMMAND, ['{"version": "v2.12.2"}'])
    proc_mock.set_output(["git", "--version"], ["git version 2.37.1 (Apple Git-137.1)"])
    proc_mock.set_output(["python", "--version"], ["Python 3.10.0"])
    proc_mock.set_output(["python3", "--version"], ["Python 3.11.0"])
    proc_mock.set_output(["pipx", "--version"], ["1.1.0"])
    proc_mock.set_output(["poetry", "--version"], ["blah blah", "", "Poetry (version 1.2.2)"])
    proc_mock.set_output(["node", "--version"], ["v18.12.1"])
    proc_mock.set_output(["npm", "--version"], ["8.19.2"])
    proc_mock.set_output(["npm.cmd", "--version"], ["8.19.2"])


def mock_shutil_which(python_command_name: str) -> str:
    if python_command_name == "python":
        return "/usr/local/bin/python"
    if python_command_name == "python3":
        return "/usr/local/bin/python3"
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


@pytest.mark.usefixtures("_mock_doctor_dependencies")
def test_doctor_help() -> None:
    result = invoke("doctor -h")

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Darwin")
def test_doctor_with_copy(mocker: MockerFixture) -> None:
    # Mock pyclip
    mocked_os = mocker.patch("algokit.cli.doctor.pyclip.copy")
    result = invoke("doctor -c")

    assert result.exit_code == 0
    mocked_os.assert_called_once()
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.usefixtures("_mock_doctor_dependencies", "mock_platform_system")
def test_doctor_successful(request: pytest.FixtureRequest) -> None:
    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber(), namer=PyTestNamer(request))


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Darwin")
def test_doctor_with_docker_compose_version_warning(proc_mock: ProcMock) -> None:
    proc_mock.set_output(DOCKER_COMPOSE_VERSION_COMMAND, ['{"version": "v2.1.3"}'])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Darwin")
def test_doctor_with_docker_compose_version_gitpod(proc_mock: ProcMock) -> None:
    proc_mock.set_output(DOCKER_COMPOSE_VERSION_COMMAND, ['{"version": "v2.10.0-gitpod.0"}'])

    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Darwin")
def test_doctor_with_docker_compose_version_unparseable(proc_mock: ProcMock) -> None:
    proc_mock.set_output(DOCKER_COMPOSE_VERSION_COMMAND, ['{"version": "TEAPOT"}'])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


ALL_COMMANDS = [
    ["brew", "--version"],
    ["docker", "--version"],
    DOCKER_COMPOSE_VERSION_COMMAND,
    ["git", "--version"],
    ["python", "--version"],
    ["python3", "--version"],
    ["pipx", "--version"],
    ["poetry", "--version"],
    ["node", "--version"],
    ["npm", "--version"],
    ["npm.cmd", "--version"],
]


@pytest.mark.usefixtures("_mock_doctor_dependencies", "mock_platform_system")
def test_doctor_all_commands_not_found(request: pytest.FixtureRequest, proc_mock: ProcMock) -> None:
    for cmd in ALL_COMMANDS:
        proc_mock.should_fail_on(cmd[0])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber(), namer=PyTestNamer(request))


@pytest.mark.usefixtures("_mock_doctor_dependencies", "mock_platform_system")
def test_doctor_all_commands_bad_exit(request: pytest.FixtureRequest, proc_mock: ProcMock) -> None:
    for cmd in ALL_COMMANDS:
        proc_mock.should_bad_exit_on(cmd, output=["I AM A TEAPOT"])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber(), namer=PyTestNamer(request))


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Darwin")
def test_doctor_with_weird_values_on_mac(proc_mock: ProcMock) -> None:
    proc_mock.set_output(["brew", "--version"], ["Homebrew 3.6.15-31-g82d89bb"])

    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Darwin")
def test_unparseable_python_version(proc_mock: ProcMock) -> None:
    proc_mock.set_output(["python", "--version"], ["  ", "1-2-3", "  abc  "])

    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.usefixtures("_mock_doctor_dependencies", "proc_mock")
@pytest.mark.mock_platform_system("Darwin")
def test_unexpected_exception_locating_executable(mocker: MockerFixture) -> None:
    def which_throw(_cmd: str) -> None:
        raise RuntimeError("OH NO")

    mocker.patch("algokit.core.doctor.which").side_effect = which_throw

    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Darwin")
def test_npm_permission_denied(proc_mock: ProcMock) -> None:
    proc_mock.should_deny_on(["npm"])

    result = invoke("doctor")

    assert result.exit_code == 1
    verify(result.output, scrubber=make_output_scrubber())


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Darwin")
def test_new_algokit_version_available(request: pytest.FixtureRequest, mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.doctor.get_latest_github_version").return_value = "4.5.6"
    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber(), namer=PyTestNamer(request))


@pytest.mark.usefixtures("_mock_doctor_dependencies")
@pytest.mark.mock_platform_system("Windows")
def test_doctor_with_weird_values_on_windows(proc_mock: ProcMock) -> None:
    proc_mock.set_output(["git", "--version"], ["git version 2.31.0.windows.1"])
    proc_mock.set_output(["winget"], ["v1.8.1911", "Winget v1.8.1911"])
    proc_mock.should_fail_on(["npm"])
    proc_mock.set_output(["npm.cmd", "--version"], [" 16.17.0 "])

    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_output_scrubber())


def test_doctor_no_mocking() -> None:
    result = invoke("doctor")
    assert result.exception is None
