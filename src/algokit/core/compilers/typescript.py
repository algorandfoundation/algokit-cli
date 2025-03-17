from collections.abc import Iterator

from algokit.core.proc import run
from algokit.core.utils import extract_version_triple, get_npm_command

PUYATS_NPM_PACKAGE = "@algorandfoundation/puya-ts"


def find_valid_puyats_command(version: str | None) -> list[str]:
    return _find_puyats_command(version)


def _find_project_puyats_command(
    npm_command: list[str], npx_command: list[str], version: str | None
) -> list[str] | None:
    """
    Try to find PuyaTs command installed at the project level.
    """
    try:
        result = run([*npm_command, "ls"])
        if result.exit_code == 0:
            generate_command = [*npx_command, PUYATS_NPM_PACKAGE]
            for line in result.output.splitlines():
                if PUYATS_NPM_PACKAGE in line:
                    if version is not None:
                        installed_version = extract_version_triple(line)
                        if extract_version_triple(version) == installed_version:
                            return generate_command
                    else:
                        return generate_command
    except OSError:
        pass
    except ValueError:
        pass

    return None


def _find_global_puyats_command(
    npm_command: list[str], npx_command: list[str], version: str | None
) -> list[str] | None:
    """
    Try to find PuyaTs command installed globally.
    """
    return _find_project_puyats_command([*npm_command, "--global"], npx_command, version)


def _find_puyats_command(version: str | None) -> list[str]:
    """
    Find puyats command.
    First checks if a matching version is installed at the project level, then uses it.
    Then checks if a matching version is installed at the global level, then uses it.
    Otherwise, runs the matching version via npx.
    """
    npm_command = get_npm_command(
        f"Unable to find npm install so that the `{PUYATS_NPM_PACKAGE}` can be run; "
        "please install npm via https://docs.npmjs.com/downloading-and-installing-node-js-and-npm "
        "and then try `algokit compile typescript ...` again.",
    )
    npx_command = get_npm_command(
        f"Unable to find npx so that the `{PUYATS_NPM_PACKAGE}` compiler can be run; "
        "please make sure `npx` is installed and try `algokit compile typescript ...` again."
        "`npx` is automatically installed with `node` starting with version 8.2.0 and above.",
        is_npx=True,
    )

    # Try to find at project level first
    project_result = _find_project_puyats_command(npm_command, npx_command, version)
    if project_result is not None:
        try:
            puyats_version_result = run([*project_result, "--version"])
            if puyats_version_result.exit_code == 0:
                return project_result
        except OSError:
            pass  # In case of path/permission issues, continue to the next candidate

    # Try to find at global level
    global_result = _find_global_puyats_command(npm_command, npx_command, version)
    if global_result is not None:
        try:
            puyats_version_result = run([*global_result, "--version"])
            if puyats_version_result.exit_code == 0:
                return global_result
        except OSError:
            pass  # In case of path/permission issues, fall back to npx

    # When not installed or available, run via npx
    return [
        *npx_command,
        "-y",
        f"{PUYATS_NPM_PACKAGE}{'@' + version if version is not None else ''}",
    ]


def _get_candidate_puyats_commands() -> Iterator[list[str]]:
    # This function is kept for backward compatibility but isn't used in the new implementation
    npx_command = get_npm_command(
        "Unable to find `npx` to check for installed PuyaTs; continuing with other options.",
        is_npx=True,
    )
    yield [*npx_command, "-y", PUYATS_NPM_PACKAGE]
