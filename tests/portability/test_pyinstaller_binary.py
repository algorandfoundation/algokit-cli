import logging
import subprocess
import sys
import time
from os import environ

import pytest

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.pyinstaller_binary_tests


def command_str_to_list(command: str) -> list[str]:
    return command.split(" ")


@pytest.mark.parametrize(
    ("command", "exit_codes"),
    [
        (command_str_to_list("--help"), [0]),
        (command_str_to_list("doctor"), [0]),
        (command_str_to_list("task vanity-address PY"), [0]),
    ],
)
def test_non_interactive_algokit_commands(
    command: list[str], exit_codes: list[int], cli_path: str, tmp_path_factory: pytest.TempPathFactory
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    execution_result = subprocess.run([cli_path, *command], capture_output=True, text=True, check=False, cwd=cwd)
    logger.info(f"Command {command} returned {execution_result.stdout}")

    # Parts of doctor will fail in CI on macOS and windows on github actions since docker isn't available by default
    if "doctor" in command and sys.platform in ["darwin", "windows"] and environ.get("CI"):
        exit_codes.append(1)

    assert execution_result.returncode in exit_codes, f"Command {command} failed with {execution_result.stderr}"


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

    full_output = ""
    while process.poll() is None and process.stdout and process.stdin:
        output = process.stdout.readline()
        full_output += output  # Accumulate the output
        logger.debug(output.strip())  # Log each line of stdout in real-time

        if "y/n" in output.lower():  # adjust this as needed based on the exact prompt text
            answer = "y\n"
            process.stdin.write(answer)
            process.stdin.flush()

        time.sleep(0.1)

    # After the process ends, log the full stdout
    logger.info(f"Command init returned:\n{full_output}")
    assert process.returncode == 0, f"Command init failed with {process.stderr}"
