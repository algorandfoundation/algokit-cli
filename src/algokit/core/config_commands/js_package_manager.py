import enum
import logging

import click
import questionary

from algokit.core.conf import get_app_config_dir

logger = logging.getLogger(__name__)

JS_PACKAGE_MANAGER_CONFIG_FILE = get_app_config_dir() / "default-js-package-manager"


class JSPackageManager(str, enum.Enum):
    NPM = "npm"
    PNPM = "pnpm"

    def __str__(self) -> str:
        return self.value


def get_js_package_manager() -> str | None:
    """Get the default JavaScript package manager for use by AlgoKit CLI.
    None implies it has not been set yet, likely to be first time user.
    """

    if JS_PACKAGE_MANAGER_CONFIG_FILE.exists():
        return JS_PACKAGE_MANAGER_CONFIG_FILE.read_text().strip()
    return None


def save_js_package_manager(manager: str) -> None:
    if manager not in JSPackageManager:
        raise ValueError(f"Invalid JavaScript package manager: {manager}")
    JS_PACKAGE_MANAGER_CONFIG_FILE.write_text(manager)


@click.command("js-package-manager", short_help="Configure the default JavaScript package manager for AlgoKit.")
@click.argument("package_manager", required=False, type=click.Choice([JSPackageManager.NPM, JSPackageManager.PNPM]))
def js_package_manager_configuration_command(*, package_manager: str | None) -> None:
    """Set the default JavaScript package manager for use by AlgoKit CLI."""

    if package_manager is None:
        current_manager = get_js_package_manager() or JSPackageManager.NPM
        choices = [
            f"npm {'(active)' if current_manager == JSPackageManager.NPM else ''}".strip(),
            f"pnpm {'(active)' if current_manager == JSPackageManager.PNPM else ''}".strip(),
        ]
        manager = questionary.select(
            "Which JavaScript package manager would you prefer `bootstrap` command to use by default?", choices=choices
        ).ask()
        if manager is None:
            raise click.ClickException("No valid JavaScript package manager selected. Aborting...")
        package_manager = manager.split()[0].lower()

    save_js_package_manager(package_manager)
    logger.info(f"JavaScript package manager set to `{package_manager}`")
