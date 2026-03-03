from collections.abc import Iterator

from algokit.core.proc import run
from algokit.core.utils import extract_version_triple, find_valid_x_command, get_tool_run_command


def find_valid_puyapy_command(version: str | None) -> list[str]:
    return _find_puyapy_command_at_version(version) if version is not None else _find_puyapy_command()


def _find_puyapy_command_at_version(version: str) -> list[str]:
    """
    Find puyapy command with a specific version.
    If the puyapy version isn't installed, run it via uvx/pipx.
    """
    for puyapy_command in _get_candidate_puyapy_commands():
        try:
            puyapy_version_result = run([*puyapy_command, "--version"])
        except OSError:
            pass  # in case of path/permission issues, go to next candidate
        else:
            if puyapy_version_result.exit_code == 0 and (
                extract_version_triple(version) == extract_version_triple(puyapy_version_result.output)
            ):
                return puyapy_command

    pipx_command = find_valid_x_command(
        "Unable to find uvx or pipx so that `PuyaPy` can be run; "
        "please install uv via https://docs.astral.sh/uv/ "
        "and then try `algokit compile python ...` again."
    )

    return get_tool_run_command(pipx_command, spec=f"puyapy=={version}", binary="puyapy")


def _find_puyapy_command() -> list[str]:
    """
    Find puyapy command.
    If puyapy isn't installed, run the latest version via uvx/pipx.
    """
    for puyapy_command in _get_candidate_puyapy_commands():
        try:
            puyapy_help_result = run([*puyapy_command, "--version"])
        except OSError:
            pass  # in case of path/permission issues, go to next candidate
        else:
            if puyapy_help_result.exit_code == 0:
                return puyapy_command

    pipx_command = find_valid_x_command(
        "Unable to find uvx or pipx so that `PuyaPy` can be run; "
        "please install uv via https://docs.astral.sh/uv/ "
        "and then try `algokit compile python ...` again."
    )
    return get_tool_run_command(pipx_command, spec="puyapy", binary="puyapy")


def _get_candidate_puyapy_commands() -> Iterator[list[str]]:
    yield ["uv", "run", "puyapy"]
    yield ["poetry", "run", "puyapy"]
    yield ["puyapy"]
