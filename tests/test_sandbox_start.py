from pathlib import Path
from subprocess import CompletedProcess

import click.testing
from approvaltests import verify  # type: ignore
from click.testing import CliRunner
from pytest_mock import MockerFixture


def get_verify_output(stdout: str, additional_name: str, additional_output: str):
    return f"""{stdout}----
{additional_name}:
----
{additional_output}"""


def invoke(args: str) -> click.testing.Result:
    from algokit.cli import algokit

    runner = CliRunner(mix_stderr=False)
    assert isinstance(algokit, click.BaseCommand)
    return runner.invoke(algokit, f"-v --no-color {args}")


def get_run_mock_call(fail_on: list[str] | None = None):
    def run(cmd: list[str], *_, **__) -> CompletedProcess:
        should_fail = fail_on and fail_on == cmd
        return CompletedProcess(cmd, -1 if should_fail else 0, "STDOUT", "STDERR")

    return run


def test_sandbox_start(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call()
    mocker.patch("algokit.core.conf.get_app_config_dir").return_value = tmp_path

    result = invoke("sandbox start")

    assert result.exit_code == 0
    verify(
        get_verify_output(
            result.stdout.replace(str(tmp_path), "{app_config}"),
            "{app_config}/sandbox/docker-compose.yml",
            (tmp_path / "sandbox" / "docker-compose.yml").read_text(),
        )
    )


def test_sandbox_start_without_docker(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call(fail_on=["docker"])
    mocker.patch("algokit.core.conf.get_app_config_dir").return_value = tmp_path

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(get_verify_output(result.stdout, "STDERR", result.stderr))


def test_sandbox_start_without_docker_compose(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call(fail_on=["docker", "compose"])
    mocker.patch("algokit.core.conf.get_app_config_dir").side_effect = tmp_path

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(get_verify_output(result.stdout, "STDERR", result.stderr))


def test_sandbox_start_without_docker_engine_running(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("subprocess.run").side_effect = get_run_mock_call(fail_on=["docker", "ps"])
    mocker.patch("algokit.core.conf.get_app_config_dir").side_effect = tmp_path

    result = invoke("sandbox start")

    assert result.exit_code == 1
    verify(get_verify_output(result.stdout, "STDERR", result.stderr))
