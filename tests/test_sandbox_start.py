import dataclasses
import subprocess
from pathlib import Path
from subprocess import CompletedProcess

import click.testing
import pytest
from approvaltests import verify  # type: ignore
from click.testing import CliRunner
from pytest_mock import MockerFixture


def get_verify_output(stdout: str, additional_name: str, additional_output: str):
    return f"""{stdout}----
{additional_name}:
----
{additional_output}"""


@dataclasses.dataclass
class ClickInvokeResult:
    exit_code: int
    output: str


def invoke(args: str) -> ClickInvokeResult:
    from algokit.cli import algokit

    runner = CliRunner()
    cwd = Path.cwd()
    assert isinstance(algokit, click.BaseCommand)
    result = runner.invoke(algokit, f"-v --no-color {args}")
    output = result.stdout.replace(str(cwd), "{current_working_directory}")
    return ClickInvokeResult(exit_code=result.exit_code, output=output)


@dataclasses.dataclass
class AppDirs:
    app_config_dir: Path
    app_state_dir: Path


@pytest.fixture()
def tmp_app_dir(mocker: MockerFixture, tmp_path: Path) -> AppDirs:
    app_config_dir = tmp_path / "config"
    app_config_dir.mkdir()
    mocker.patch("algokit.core.conf.get_app_config_dir").return_value = app_config_dir

    app_state_dir = tmp_path / "state"
    app_state_dir.mkdir()
    mocker.patch("algokit.core.conf.get_app_state_dir").return_value = app_state_dir

    return AppDirs(app_config_dir=app_config_dir, app_state_dir=app_state_dir)


def get_run_mock_call(fail_on: list[str] | None = None):
    def run(cmd: list[str], *_, **__) -> subprocess.CompletedProcess:
        should_fail = fail_on and fail_on == cmd
        return CompletedProcess(cmd, -1 if should_fail else 0, "STDOUT+STDERR")

    return run


def get_run_mock_error_call(fail_on: list[str] | None = None):
    def run(cmd: list[str], *_, **__) -> subprocess.CompletedProcess:
        should_fail = fail_on and fail_on == cmd
        if should_fail:
            raise FileNotFoundError(f"No such file or directory: {cmd[0]}")
        return CompletedProcess(cmd, 0, "STDOUT+STDERR")

    return run


def test_sandbox_start(tmp_app_dir: AppDirs, mocker: MockerFixture):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call()

    result = invoke("sandbox start")

    assert result.exit_code == 0
    verify(
        get_verify_output(
            result.output.replace(str(tmp_app_dir.app_config_dir), "{app_config}"),
            "{app_config}/sandbox/docker-compose.yml",
            (tmp_app_dir.app_config_dir / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


def test_sandbox_start_without_docker(tmp_app_dir: AppDirs, mocker: MockerFixture):
    mocker.patch("subprocess.run").side_effect = get_run_mock_error_call(fail_on=["docker", "compose", "version"])

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_start_without_docker_compose(tmp_app_dir: AppDirs, mocker: MockerFixture):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call(fail_on=["docker", "compose", "version"])

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_start_without_docker_engine_running(tmp_app_dir: AppDirs, mocker: MockerFixture):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call(fail_on=["docker", "version"])

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(result.output)
