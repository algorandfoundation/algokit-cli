from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

from approvaltests import verify  # type: ignore
from click.testing import CliRunner
from pytest_mock import MockerFixture

from algokit.cli import algokit


def verify_output(stdout: str, additional_name: str | None = None, additional_output: str | None = None):
    return (
        f"""{stdout}----
{additional_name}:
----
{additional_output}"""
        if additional_name
        else stdout
    )


def invoke(args: str):
    runner = CliRunner(mix_stderr=False)
    return runner.invoke(algokit, ["-v", "--no-color", *args.split()])  # type: ignore


def get_run_mock_call(fail_on: str | None = None):
    def run(cmd: list[str], **args: list[Any]):
        command = " ".join(cmd)
        return CompletedProcess([], -1 if fail_on and command == fail_on else 0, "STDOUT".encode(), "STDERR".encode())

    return run


def test_sandbox_start(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call()
    mocker.patch("algokit.core.conf.get_app_config_dir").return_value = tmp_path

    result = invoke("sandbox start")

    assert result.exit_code == 0
    verify(
        verify_output(
            result.stdout.replace(str(tmp_path), "{app_config}"),
            "{app_config}/docker-compose.yml",
            (tmp_path / "docker-compose.yml").read_text(),
        )
    )


def test_sandbox_start_without_docker(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call(fail_on="docker")
    mocker.patch("algokit.core.conf.get_app_config_dir").return_value = tmp_path

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(verify_output(result.stdout, "STDERR", result.stderr))


def test_sandbox_start_without_docker_compose(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call(fail_on="docker compose")
    mocker.patch("algokit.core.conf.get_app_config_dir").side_effect = tmp_path

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(verify_output(result.stdout, "STDERR", result.stderr))


def test_sandbox_start_without_docker_engine_running(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call(fail_on="docker ps")
    mocker.patch("algokit.core.conf.get_app_config_dir").side_effect = tmp_path

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(verify_output(result.stdout, "STDERR", result.stderr))
