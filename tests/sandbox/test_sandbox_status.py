from approvaltests import verify
from utils.app_dir_mock import AppDirs
from utils.click_invoker import invoke
from utils.exec_mock import ExecMock


def get_verify_output(stdout: str, additional_name: str, additional_output: str) -> str:
    return f"""{stdout}----
{additional_name}:
----
{additional_output}"""


def test_sandbox_status_successful(app_dir_mock: AppDirs, exec_mock: ExecMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")

    exec_mock.set_output(
        "docker compose ps --all --format json",
        [
            '[{"ID":"00e93d3db91d964d1b2bcf444c938140dc6b43398380374eaac8510f45381973","Name":"algokit_algod","Command":"start.sh","Project":"algokit_sandbox","Service":"algod","State":"running","Health":"","ExitCode":0,"Publishers":[{"URL":"0.0.0.0","TargetPort":4001,"PublishedPort":4001,"Protocol":"tcp"},{"URL":"0.0.0.0","TargetPort":4002,"PublishedPort":4002,"Protocol":"tcp"},{"URL":"0.0.0.0","TargetPort":9392,"PublishedPort":9392,"Protocol":"tcp"}]},{"ID":"a242581a65f7e49d376bff9fd8d2288cdd85a28a264657d73db84dbeef6155b7","Name":"algokit_indexer","Command":"/tmp/start.sh","Project":"algokit_sandbox","Service":"indexer","State":"running","Health":"","ExitCode":0,"Publishers":[{"URL":"0.0.0.0","TargetPort":8980,"PublishedPort":8980,"Protocol":"tcp"}]},{"ID":"17aea624f2d448cc3c39f8e399b62d4e0f53fb23a5357d71cd11729720a2ba44","Name":"algokit_postgres","Command":"docker-entrypoint.shpostgres","Project":"algokit_sandbox","Service":"indexer-db","State":"running","Health":"","ExitCode":0,"Publishers":[{"URL":"","TargetPort":5432,"PublishedPort":0,"Protocol":"tcp"}]}]'
        ],
    )

    result = invoke("sandbox status")

    assert result.exit_code == 0
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_status_failure(app_dir_mock: AppDirs, exec_mock: ExecMock):
    (app_dir_mock.app_config_dir / "sandbox").mkdir()
    (app_dir_mock.app_config_dir / "sandbox" / "docker-compose.yml").write_text("existing")
    exec_mock.should_bad_exit_on("docker compose stop")

    result = invoke("sandbox status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_status_no_existing_definition(app_dir_mock: AppDirs, exec_mock: ExecMock):
    result = invoke("sandbox status")

    assert result.exit_code == 1
    verify(result.output.replace(str(app_dir_mock.app_config_dir), "{app_config}").replace("\\", "/"))


def test_sandbox_status_without_docker(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_fail_on("docker compose version")

    result = invoke("sandbox status")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_status_without_docker_compose(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_bad_exit_on("docker compose version")

    result = invoke("sandbox status")

    assert result.exit_code == 1
    verify(result.output)


def test_sandbox_status_without_docker_engine_running(app_dir_mock: AppDirs, exec_mock: ExecMock):
    exec_mock.should_bad_exit_on("docker version")

    result = invoke("sandbox status")

    assert result.exit_code == 1
    verify(result.output)
