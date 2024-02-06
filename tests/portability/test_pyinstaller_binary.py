import logging
import subprocess
import time

import pytest

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.pyinstaller_binary_tests


def command_str_to_list(command: str) -> list[str]:
    return command.split(" ")


@pytest.mark.parametrize(
    "command",
    [
        command_str_to_list("--help"),
        command_str_to_list("doctor"),
        command_str_to_list("task vanity-address PY"),
    ],
)
def test_non_interactive_algokit_commands(
    command: list[str], cli_path: str, tmp_path_factory: pytest.TempPathFactory
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    execution_result = subprocess.run([cli_path, *command], capture_output=True, text=True, check=False, cwd=cwd)
    logger.info(f"Command {command} returned {execution_result.stdout}")
    assert execution_result.returncode == 0, f"Command {command} failed with {execution_result.stderr}"


def test_algokit_init(cli_path: str, tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    command = command_str_to_list(
        "init --name testproject "
        "--UNSAFE-SECURITY-accept-template-url "
        "--template-url https://github.com/algorandfoundation/algokit-fullstack-template "
        "--template-url-ref=python_path --no-git --no-ide --defaults "
        "-a deployment_language python -a ide_vscode false -a preset_name starter"
    )

    process = subprocess.Popen(
        [cli_path, *command],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=cwd,
    )

    # Write 'y' to stdin while the process is still running
    while process.poll() is None and process.stdout and process.stdin:
        output = process.stdout.readline().lower()
        logger.debug(
            output,
        )  # print stdout in real-time, without adding an extra newline

        if "y/n" in output:  # adjust this as needed based on the exact prompt text
            answer = "y\n"
            process.stdin.write(answer)
            process.stdin.flush()

        time.sleep(0.1)

    logger.info(f"Command init returned {process.stdout}")
    assert process.returncode == 0, f"Command init failed with {process.stderr}"
