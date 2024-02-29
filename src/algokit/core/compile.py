from collections.abc import Iterator

from algokit.core.proc import run
from algokit.core.utils import extract_version_triple, find_valid_pipx_command


def find_valid_puyapy_command(version: str | None) -> list[str]:
    return (
        _find_puya_command_with_version_specifier(version)
        if version is not None
        else _find_puya_command_without_version_specifier()
    )


def _find_puya_command_with_version_specifier(version: str) -> list[str]:
    for puyapy_command in _get_candidates_puyapy_commands():
        try:
            puyapy_version_result = run([*puyapy_command, "--version"])
        except OSError:
            pass  # in case of path/permission issues, go to next candidate
        else:
            if puyapy_version_result.exit_code == 0 and (
                extract_version_triple(version) == extract_version_triple(puyapy_version_result.output)
            ):
                return puyapy_command

    pipx_command = find_valid_pipx_command(
        "Unable to find pipx install so that `PuyaPy` compiler can be installed; "
        "please install pipx via https://pypa.github.io/pipx/ "
        "and then try `algokit compile py ...` again."
    )

    return [
        *pipx_command,
        "run",
        f"puya=={version}",
    ]


def _find_puya_command_without_version_specifier() -> list[str]:
    for puyapy_command in _get_candidates_puyapy_commands():
        try:
            puyapy_help_result = run([*puyapy_command, "-h"])
        except OSError:
            pass  # in case of path/permission issues, go to next candidate
        else:
            if puyapy_help_result.exit_code == 0:
                return puyapy_command

    pipx_command = find_valid_pipx_command(
        "Unable to find pipx install so that `PuyaPy` compiler can be installed; "
        "please install pipx via https://pypa.github.io/pipx/ "
        "and then try `algokit compile py ...` again."
    )
    _install_puyapy_with_pipx(pipx_command)
    return ["puyapy"]


def _install_puyapy_with_pipx(pipx_command: list[str]) -> None:
    run(
        [
            *pipx_command,
            "install",
            "puya",
        ],
        bad_return_code_error_message=(
            "Unable to install puya via pipx; please install puya manually and try `algokit compile py ...` again."
        ),
    )


def _get_candidates_puyapy_commands() -> Iterator[list[str]]:
    # when puya is installed at the project level
    yield ["poetry", "run", "puyapy"]
    # when puya is installed at the global level
    yield ["puyapy"]
