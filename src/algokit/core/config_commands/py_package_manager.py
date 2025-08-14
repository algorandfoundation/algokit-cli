import enum
import logging

import click
import questionary

from algokit.core.conf import get_app_config_dir

logger = logging.getLogger(__name__)

PY_PACKAGE_MANAGER_CONFIG_FILE = get_app_config_dir() / "default-py-package-manager"


class PyPackageManager(str, enum.Enum):
    POETRY = "poetry"
    UV = "uv"

    def __str__(self) -> str:
        return self.value


def get_py_package_manager() -> str | None:
    """Get the default Python package manager for use by AlgoKit CLI.
    None implies it has not been set yet, likely to be first time user.
    """

    if PY_PACKAGE_MANAGER_CONFIG_FILE.exists():
        return PY_PACKAGE_MANAGER_CONFIG_FILE.read_text().strip()
    return None


def save_py_package_manager(manager: str) -> None:
    if manager not in PyPackageManager:
        raise ValueError(f"Invalid Python package manager: {manager}")
    PY_PACKAGE_MANAGER_CONFIG_FILE.write_text(manager)


@click.command("py-package-manager", short_help="Configure the default Python package manager for AlgoKit.")
@click.argument("package_manager", required=False, type=click.Choice([PyPackageManager.POETRY, PyPackageManager.UV]))
def py_package_manager_configuration_command(*, package_manager: str | None) -> None:
    """Set the default Python package manager for use by AlgoKit CLI."""

    if package_manager is None:
        current_manager = get_py_package_manager() or PyPackageManager.POETRY
        choices = [
            f"poetry {'(active)' if current_manager == PyPackageManager.POETRY else ''}".strip(),
            f"uv {'(active)' if current_manager == PyPackageManager.UV else ''}".strip(),
        ]
        manager = questionary.select(
            "Which Python package manager would you prefer `bootstrap` command to use by default?", choices=choices
        ).ask()
        if manager is None:
            raise click.ClickException("No valid Python package manager selected. Aborting...")
        package_manager = manager.split()[0].lower()

    save_py_package_manager(package_manager)
    logger.info(f"Python package manager set to `{package_manager}`")
