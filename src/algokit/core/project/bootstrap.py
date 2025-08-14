import logging
import os
from pathlib import Path

import click
import questionary
from packaging import version

from algokit.core import proc, questionary_extensions
from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config, get_current_package_version
from algokit.core.config_commands.js_package_manager import (
    JSPackageManager,
    get_js_package_manager,
    save_js_package_manager,
)
from algokit.core.config_commands.py_package_manager import (
    PyPackageManager,
    get_py_package_manager,
    save_py_package_manager,
)
from algokit.core.utils import find_valid_pipx_command, is_windows

ENV_TEMPLATE_PATTERN = ".env*.template"
MAX_BOOTSTRAP_DEPTH = 2
logger = logging.getLogger(__name__)


def _has_pyproject_toml(project_dir: Path) -> bool:
    return (project_dir / "pyproject.toml").exists()


def _get_py_package_manager_override(project_dir: Path) -> str | None:
    """Get Python package manager override from .algokit.toml configuration."""
    algokit_config = get_algokit_config(project_dir=project_dir)
    if algokit_config and "package_manager" in algokit_config and "python" in algokit_config["package_manager"]:
        manager = algokit_config["package_manager"]["python"]
        logger.debug(f"Using Python package manager from .algokit.toml: {manager}")
        return str(manager)
    return None


def _get_js_package_manager_override(project_dir: Path) -> str | None:
    """Get JavaScript package manager override from .algokit.toml configuration."""
    algokit_config = get_algokit_config(project_dir=project_dir)
    if algokit_config and "package_manager" in algokit_config and "javascript" in algokit_config["package_manager"]:
        manager = algokit_config["package_manager"]["javascript"]
        logger.debug(f"Using JavaScript package manager from .algokit.toml: {manager}")
        return str(manager)
    return None


def is_uv_project(project_dir: Path) -> bool:
    uv_path = project_dir / "uv.lock"
    return uv_path.exists()


def _has_python_project(project_dir: Path) -> bool:
    """Check if the directory contains a Python project."""
    poetry_path = project_dir / "poetry.toml"
    pyproject_path = project_dir / "pyproject.toml"
    return poetry_path.exists() or pyproject_path.exists()


def _has_javascript_project(project_dir: Path) -> bool:
    """Check if the directory contains a JavaScript project."""
    return (project_dir / "package.json").exists()


def _determine_python_package_manager(project_dir: Path) -> str:
    """
    Determine Python package manager with proper precedence:
    1. Project override (.algokit.toml) - Explicit project configuration
    2. User preference (algokit config) - User's explicit choice
    3. Smart defaults (project structure) - Only when no preference exists
    4. Interactive prompt - Falls back to user input and saves preference
    """

    # 1. Project-specific override (highest priority)
    override = _get_py_package_manager_override(project_dir)
    if override:
        return override

    # 2. User's global preference (respects user's explicit choice)
    user_preference = get_py_package_manager()
    if user_preference:
        return user_preference

    # 3. Smart defaults based on project structure (only when no user preference)
    poetry_path = project_dir / "poetry.toml"
    pyproject_path = project_dir / "pyproject.toml"

    if poetry_path.exists():
        # Standalone poetry.toml suggests Poetry
        return PyPackageManager.POETRY

    if pyproject_path.exists() and "[tool.poetry]" in pyproject_path.read_text("utf-8"):
        # pyproject.toml with [tool.poetry] section suggests Poetry
        return PyPackageManager.POETRY

    # 4. Interactive prompt for first-time users
    manager = questionary.select(
        "Which Python package manager would you prefer `bootstrap` command to use?",
        choices=[PyPackageManager.POETRY, PyPackageManager.UV],
    ).ask()
    if manager is None:
        # Default to Poetry if user cancels
        manager = PyPackageManager.POETRY
    save_py_package_manager(manager)
    return str(manager)


def _determine_javascript_package_manager(project_dir: Path) -> str:
    """
    Determine JavaScript package manager with proper precedence:
    1. Project override (.algokit.toml) - Explicit project configuration
    2. User preference (algokit config) - User's explicit choice
    3. Smart defaults (lock files) - Only when no preference exists
    4. Interactive prompt - Falls back to user input and saves preference
    """

    # 1. Project-specific override (highest priority)
    override = _get_js_package_manager_override(project_dir)
    if override:
        return override

    # 2. User's global preference (respects user's explicit choice)
    user_preference = get_js_package_manager()
    if user_preference:
        return user_preference

    # 3. Smart defaults based on lock files (only when no user preference)
    if (project_dir / "pnpm-lock.yaml").exists():
        return JSPackageManager.PNPM

    if (project_dir / "package-lock.json").exists():
        return JSPackageManager.NPM

    # 4. Interactive prompt for first-time users
    manager = questionary_extensions.prompt_select(
        "Which JavaScript package manager would you prefer `bootstrap` command to use?",
        *[questionary.Choice(title=npm.value, value=npm) for npm in JSPackageManager],
    )
    if manager is None:
        # Default to NPM if user cancels
        manager = JSPackageManager.NPM
    save_js_package_manager(manager)
    return str(manager)


def _bootstrap_python_project(project_dir: Path, manager: str) -> None:
    """Bootstrap a Python project with the specified package manager."""
    if manager == PyPackageManager.UV:
        logger.debug("Running `algokit project bootstrap uv`")
        bootstrap_uv(project_dir)
    else:  # Default to Poetry for backward compatibility
        logger.debug("Running `algokit project bootstrap poetry`")
        bootstrap_poetry(project_dir)


def _bootstrap_javascript_project(project_dir: Path, manager: str, *, ci_mode: bool) -> None:
    """Bootstrap a JavaScript project with the specified package manager."""
    if manager == JSPackageManager.NPM:
        logger.debug("Running `algokit project bootstrap npm`")
        bootstrap_npm(project_dir, ci_mode=ci_mode)
    elif manager == JSPackageManager.PNPM:
        logger.debug("Running `algokit project bootstrap pnpm`")
        bootstrap_pnpm(project_dir, ci_mode=ci_mode)


def bootstrap_any(project_dir: Path, *, ci_mode: bool) -> None:
    """Bootstrap a project with elegant package manager selection."""

    logger.debug(f"Checking {project_dir} for bootstrapping needs")

    # Environment files
    if next(project_dir.glob(ENV_TEMPLATE_PATTERN), None):
        logger.debug("Running `algokit project bootstrap env`")
        bootstrap_env(project_dir, ci_mode=ci_mode)

    # Python projects
    if _has_python_project(project_dir):
        manager = _determine_python_package_manager(project_dir)
        _bootstrap_python_project(project_dir, manager)

    # JavaScript projects
    if _has_javascript_project(project_dir):
        manager = _determine_javascript_package_manager(project_dir)
        _bootstrap_javascript_project(project_dir, manager, ci_mode=ci_mode)


def bootstrap_any_including_subdirs(  # noqa: PLR0913
    base_path: Path,
    *,
    ci_mode: bool,
    max_depth: int = MAX_BOOTSTRAP_DEPTH,
    depth: int = 0,
    project_names: list[str] | None = None,
    project_type: str | None = None,
) -> None:
    if depth > max_depth:
        return

    config_project = (get_algokit_config(project_dir=base_path) or {}).get("project", {})
    skip = bool(config_project) and (
        (project_type and config_project.get("type") != project_type)
        or (project_names and config_project.get("name") not in project_names)
    )

    if not skip:
        bootstrap_any(base_path, ci_mode=ci_mode)

    for sub_dir in sorted(base_path.iterdir()):  # sort needed for test output ordering
        if sub_dir.is_dir() and sub_dir.name.lower() not in [".venv", "node_modules", "__pycache__"]:
            bootstrap_any_including_subdirs(
                sub_dir,
                ci_mode=ci_mode,
                max_depth=max_depth,
                depth=depth + 1,
                project_names=project_names,
                project_type=project_type,
            )
        else:
            logger.debug(f"Skipping {sub_dir}")


def bootstrap_env(project_dir: Path, *, ci_mode: bool) -> None:
    # List all .env*.template files in the directory
    env_template_paths = sorted(project_dir.glob(ENV_TEMPLATE_PATTERN))

    # If no template files found, log it
    if not env_template_paths:
        logger.info("No .env or .env.{network_name}.template files found; nothing to do here, skipping bootstrap.")
        return

    # Process each template file
    for env_template_path in env_template_paths:
        # Determine the output file name (strip .template suffix)
        env_path = Path(env_template_path).with_suffix("")

        if env_path.exists():
            logger.info(f"{env_path.name} already exists; skipping bootstrap of {env_path.name}")
            continue

        logger.debug(f"{env_path} doesn't exist yet")
        logger.debug(f"{env_template_path} exists")
        logger.info(f"Copying {env_template_path} to {env_path} and prompting for empty values")

        # find all empty values in .env file and prompt the user for a value
        with (
            Path(env_template_path).open(encoding="utf-8") as env_template_file,
            env_path.open(mode="w", encoding="utf-8") as env_file,
        ):
            comment_lines: list[str] = []
            for line in env_template_file:
                # strip newline character(s) from end of line for simpler handling
                stripped_line = line.strip()
                # if it is a comment line, keep it in var and continue
                if stripped_line.startswith("#"):
                    comment_lines.append(line)
                    env_file.write(line)
                # keep blank lines in output but don't accumulate them in comments
                elif not stripped_line:
                    env_file.write(line)
                else:
                    # lines not blank and not empty
                    var_name, *var_value = stripped_line.split("=", maxsplit=1)
                    # if it is an empty value, the user should be prompted for value with the comment line above
                    if var_value and not var_value[0]:
                        var_name = var_name.strip()
                        if not ci_mode:
                            logger.info("".join(comment_lines))
                            new_value = questionary_extensions.prompt_text(f"Please provide a value for {var_name}:")
                            env_file.write(f"{var_name}={new_value}\n")
                        # In CI mode, we _don't_ prompt for values, because... it's CI
                        # we can omit the line entirely in the case of blank value,
                        # and just to be nice we can check to make sure the var is defined in the current
                        # env and if not, print a warning
                        # note that due to the multiple env files, this might be an aberrant warning as
                        # it might be for an .env<name>.template that is not used in the current CI process?
                        elif var_name not in os.environ:
                            logger.warning(f"Prompt skipped for {var_name} due to CI mode, but this value is not set")
                    else:  # this is a line with value
                        env_file.write(line)
                    comment_lines = []


def bootstrap_poetry(project_dir: Path) -> None:
    try:
        proc.run(
            ["poetry", "--version"],
            bad_return_code_error_message="poetry --version failed, please check your poetry install",
        )
        try_install_poetry = False
    except OSError:
        try_install_poetry = True

    if try_install_poetry:
        logger.info("Poetry not found; attempting to install it...")
        if not questionary_extensions.prompt_confirm(
            "We couldn't find `poetry`; can we install it for you via pipx so we can install Python dependencies?",
            default=True,
        ):
            raise click.ClickException(
                "Unable to install poetry via pipx; please install poetry "
                "manually via https://python-poetry.org/docs/ and try `algokit project bootstrap poetry` again."
            )
        pipx_command = find_valid_pipx_command(
            "Unable to find pipx install so that poetry can be installed; "
            "please install pipx via https://pypa.github.io/pipx/ "
            "and then try `algokit project bootstrap poetry` again."
        )
        proc.run(
            [*pipx_command, "install", "poetry"],
            bad_return_code_error_message=(
                "Unable to install poetry via pipx; please install poetry "
                "manually via https://python-poetry.org/docs/ and try `algokit project bootstrap poetry` again."
            ),
        )

    logger.info("Installing Python dependencies and setting up Python virtual environment via Poetry")
    try:
        proc.run(["poetry", "install"], stdout_log_level=logging.INFO, cwd=project_dir)
    except OSError as e:
        if try_install_poetry:
            raise click.ClickException(
                "Unable to access Poetry on PATH after installing it via pipx; "
                "check pipx installations are on your path by running `pipx ensurepath` "
                "and try `algokit project bootstrap poetry` again."
            ) from e
        raise  # unexpected error, we already ran without IOError before


def bootstrap_npm(project_dir: Path, *, ci_mode: bool) -> None:
    def get_install_command(*, ci_mode: bool) -> list[str]:
        has_package_lock = (project_dir / "package-lock.json").exists()
        if ci_mode and not has_package_lock:
            raise click.ClickException(
                "Cannot run `npm ci` because `package-lock.json` is missing. "
                "Please run `npm install` instead and commit it to your source control."
            )
        return ["ci" if ci_mode else "install"]

    package_json_path = project_dir / "package.json"
    if not package_json_path.exists():
        logger.info(f"{package_json_path} doesn't exist; nothing to do here, skipping bootstrap of npm")
    else:
        logger.info("Installing npm dependencies")
        cmd = ["npm" if not is_windows() else "npm.cmd", *get_install_command(ci_mode=ci_mode)]
        try:
            proc.run(
                cmd,
                stdout_log_level=logging.INFO,
                cwd=project_dir,
            )
        except OSError as e:
            raise click.ClickException(
                f"Failed to run `{' '.join(cmd)}` for {package_json_path}. Is npm installed and available on PATH?"
            ) from e


def bootstrap_pnpm(project_dir: Path, *, ci_mode: bool) -> None:
    def get_install_command(*, ci_mode: bool) -> list[str]:
        # PNPM auto-detects CI environments and uses appropriate behavior automatically
        # Only check for lockfile existence in CI mode for better error messages
        if ci_mode:
            has_package_lock = (project_dir / "pnpm-lock.yaml").exists()
            if not has_package_lock:
                raise click.ClickException(
                    "Cannot run in CI mode because `pnpm-lock.yaml` is missing. "
                    "Please run `pnpm install` to generate the lockfile and commit it to your source control."
                )
        return ["install"]  # Let PNPM handle CI detection automatically

    package_json_path = project_dir / "package.json"
    if not package_json_path.exists():
        logger.info(f"{package_json_path} doesn't exist; nothing to do here, skipping bootstrap of pnpm")
    else:
        logger.info("Installing pnpm dependencies")
        cmd = ["pnpm" if not is_windows() else "pnpm.cmd", *get_install_command(ci_mode=ci_mode)]
        try:
            proc.run(cmd, stdout_log_level=logging.INFO, cwd=project_dir)
        except OSError as e:
            raise click.ClickException(
                f"Failed to run `{' '.join(cmd)}` for {package_json_path}. Is pnpm installed and available on PATH?"
            ) from e


def migrate_pyproject_to_uv(project_dir: Path) -> None:
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        raise click.ClickException("pyproject.toml doesn't exist; nothing to do here, skipping migration")
    try:
        proc.run(["uvx", "migrate-to-uv"], cwd=project_dir, stdout_log_level=logging.INFO)
    except OSError as e:
        raise click.ClickException(
            "Failed to run `uvx migrate-to-uv` for pyproject.toml. Is uv installed and available on PATH?"
        ) from e


def bootstrap_uv(project_dir: Path) -> None:  # noqa: C901
    try:
        proc.run(
            ["uv", "--version"],
            bad_return_code_error_message="uv --version failed, please check your uv install",
        )
        try_install_uv = False
    except OSError:
        try_install_uv = True

    if try_install_uv:
        logger.info("UV not found; attempting to install it...")
        if not questionary_extensions.prompt_confirm(
            "We couldn't find `uv`; can we install it for you via curl so we can install Python dependencies?",
            default=True,
        ):
            raise click.ClickException(
                "Unable to install uv; please install uv "
                "manually via https://github.com/astral-sh/uv and try `algokit project bootstrap uv` again."
            )

        # Use the standalone installer as recommended in the UV docs
        if is_windows():
            cmd = ["powershell", "-ExecutionPolicy", "ByPass", "-c", "irm https://astral.sh/uv/install.ps1 | iex"]
            try:
                proc.run(
                    cmd,
                    bad_return_code_error_message=(
                        "Unable to install uv; please install uv "
                        "manually via https://github.com/astral-sh/uv and try `algokit project bootstrap uv` again."
                    ),
                )
            except Exception as e:
                raise click.ClickException(
                    "Failed to install uv. Please install it manually via "
                    "https://github.com/astral-sh/uv and try `algokit project bootstrap uv` again."
                ) from e
        else:
            # For Unix platforms, use proc.run with sh -c to handle the pipe safely
            try:
                proc.run(
                    ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
                    bad_return_code_error_message=(
                        "Unable to install uv; please install uv "
                        "manually via https://github.com/astral-sh/uv and try `algokit project bootstrap uv` again."
                    ),
                )
            except Exception as e:
                raise click.ClickException(
                    "Failed to install uv. Please install it manually via "
                    "https://github.com/astral-sh/uv and try `algokit project bootstrap uv` again."
                ) from e

    # Check if pyproject.toml contains poetry configuration
    pyproject_path = project_dir / "pyproject.toml"
    is_poetry_project = pyproject_path.exists() and "[tool.poetry]" in pyproject_path.read_text("utf-8")
    if is_poetry_project:
        if questionary_extensions.prompt_confirm(
            "Would you like to attempt to migrate the pyproject configuration to uv compliant format?\n"
            "⚠️  This will run a third-party tool (https://mkniewallner.github.io/migrate-to-uv/) "
            "that will attempt to convert your poetry project to uv. "
            "You are advised to double check the migrated file and it's recommended to run this "
            "in a version controlled repository to revert changes if needed.",
            default=False,
        ):
            migrate_pyproject_to_uv(project_dir)
        else:
            raise click.ClickException(
                "This project is configured to use Poetry. Please use `algokit project bootstrap poetry`, "
                "set poetry as default package manager via `algokit config py-package-manager`, "
                "or modify your pyproject.toml to be compatible with UV."
            )

    logger.info("Installing Python dependencies and setting up Python virtual environment via UV")
    try:
        # Sync will create/update the virtual environment and install dependencies
        proc.run(["uv", "sync"], stdout_log_level=logging.INFO, cwd=project_dir)
    except OSError as e:
        if try_install_uv:
            raise click.ClickException(
                "Unable to access UV on PATH after installing it; "
                "try restarting your terminal and running `algokit project bootstrap uv` again."
            ) from e
        raise  # unexpected error, we already ran without IOError before


def get_min_algokit_version(project_dir: Path) -> str | None:
    config = get_algokit_config(project_dir=project_dir)
    if config is None:
        return None
    try:
        return str(config["algokit"]["min_version"])
    except KeyError:
        logger.debug(f"No 'min_version' specified in {ALGOKIT_CONFIG} file.")
        return None
    except Exception as ex:
        logger.debug(f"Couldn't read algokit min_version from {ALGOKIT_CONFIG} file: {ex}", exc_info=True)
        return None


def project_minimum_algokit_version_check(project_dir: Path, *, ignore_version_check_fail: bool = False) -> None:
    """
    Checks the current version of AlgoKit against the minimum required version specified in the AlgoKit config file.
    """

    min_version = get_min_algokit_version(project_dir)
    if min_version is None:
        return
    algokit_version = get_current_package_version()
    if version.parse(algokit_version) < version.parse(min_version):
        message = (
            f"This template requires AlgoKit version {min_version} or higher, "
            f"but you have AlgoKit version {algokit_version}. Please update AlgoKit."
        )
        if ignore_version_check_fail:
            logger.warning(message)
        else:
            raise click.ClickException(message)
