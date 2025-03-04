from collections.abc import Iterator

from algokit.core.proc import run
from algokit.core.utils import extract_version_triple, get_npm_command


def find_valid_puyats_command(version: str | None) -> list[str]:
    return _find_puyats_command(version)


def _find_puyats_command(version: str | None) -> list[str]:
    """
    Find puyats command.
    If puyats isn't installed, install the latest version with pipx.
    """
    for puyats_command in _get_candidate_puyats_commands():
        try:
            puyats_help_result = run([*puyats_command, "--version"])
        except OSError:
            pass  # in case of path/permission issues, go to next candidate
        else:
            if (
                puyats_help_result.exit_code == 0
                and version is not None
                and (extract_version_triple(version) == extract_version_triple(puyats_help_result.output))
            ):
                return puyats_command

    npx_command = get_npm_command(
        "Unable to find `npx` so that the `PuyaTs` compiler can be run; "
        "please make sure `npx` is installed and try `algokit compile typescript ...` again."
        "`npx` is automatically installed with `node` starting with version 8.2.0 and above.",
        is_npx=True,
    )
    return [
        *npx_command,
        f"@algorandfoundation/puya-ts{'@' + version if version is not None else ''}",
    ]


def _get_candidate_puyats_commands() -> Iterator[list[str]]:
    # defer to npx as it first checks if puyats is installed at the project level
    # then the global level, the -y flag is used to automatically answer yes to all prompts if
    # puyats is not installed
    yield ["npx", "-y", "@algorandfoundation/puya-ts"]
