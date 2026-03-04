import logging
import platform
import sys
from pathlib import Path

import click

from algokit.cli.compile import compile_group
from algokit.cli.completions import completions_group
from algokit.cli.config import config_group
from algokit.cli.dispenser import dispenser_group
from algokit.cli.doctor import doctor_command
from algokit.cli.explore import explore_command
from algokit.cli.generate import generate_group
from algokit.cli.goal import goal_command
from algokit.cli.init import init_group
from algokit.cli.localnet import localnet_group
from algokit.cli.project import project_group
from algokit.cli.project.bootstrap import bootstrap_group
from algokit.cli.project.deploy import deploy_command
from algokit.cli.task import task_group
from algokit.core.conf import PACKAGE_NAME
from algokit.core.config_commands.version_prompt import do_version_prompt, skip_version_check_option
from algokit.core.log_handlers import color_option, verbose_option
from algokit.core.utils import find_all_on_path, is_binary_mode

_INSTALL_URL_BASE = "https://raw.githubusercontent.com/algorandfoundation/algokit-cli/main/scripts/install"
_INSTALL_URL_SH = f"{_INSTALL_URL_BASE}/install.sh"
_INSTALL_URL_PS1 = f"{_INSTALL_URL_BASE}/install.ps1"
_ADR_URL = (
    "https://github.com/algorandfoundation/algokit-cli/blob/main/"
    "docs/architecture-decisions/2025-03-03_uv_distribution.md"
)

HIDDEN_COMMANDS: dict[str, click.Command] = {"deploy": deploy_command, "bootstrap": bootstrap_group}


class CustomGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # ensures hidden commands are still invocable yet not visible in help
        if cmd_name in HIDDEN_COMMANDS:
            return HIDDEN_COMMANDS[cmd_name]

        return None


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 120,
    },
    cls=CustomGroup,
)
@click.version_option(package_name=PACKAGE_NAME)
@verbose_option
@color_option
@skip_version_check_option
def algokit(*, skip_version_check: bool) -> None:
    """
    AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.

    If you are getting started, please see the quick start tutorial: https://dev.algorand.co/getting-started/algokit-quick-start/.
    """
    if not skip_version_check:
        do_version_prompt()

    _check_binary_deprecation()


algokit.add_command(completions_group)
algokit.add_command(config_group)
algokit.add_command(doctor_command)
algokit.add_command(explore_command)
algokit.add_command(goal_command)
algokit.add_command(init_group)
algokit.add_command(localnet_group)
algokit.add_command(generate_group)
algokit.add_command(dispenser_group)
algokit.add_command(task_group)
algokit.add_command(compile_group)
algokit.add_command(project_group)


def _check_binary_deprecation() -> None:
    if not is_binary_mode():
        return

    install_cmd = (
        f"irm {_INSTALL_URL_PS1} | iex" if platform.system() == "Windows" else f"curl -fsSL {_INSTALL_URL_SH} | bash"
    )

    logger = logging.getLogger(__name__)
    logger.warning(
        "\n"
        "  WARNING: AlgoKit binary installation is being phased out.\n"
        "  Starting from the next major version, AlgoKit will be distributed via uv.\n"
        "  To migrate now, run:\n"
        "\n"
        "    %s\n"
        "\n"
        "  For more information, see:\n"
        "    %s\n",
        install_cmd,
        _ADR_URL,
    )

    algokit_paths = find_all_on_path("algokit")
    if len(algokit_paths) <= 1:
        return

    active_path = algokit_paths[0]
    current_binary_path = Path(sys.executable)
    all_paths = "\n".join(f"    - {path}" for path in algokit_paths)

    logger.warning(
        "\n"
        "  WARNING: Multiple `algokit` executables were found on PATH.\n"
        "  Active executable: %s\n"
        "  Current binary: %s\n"
        "  All PATH matches:\n"
        "%s\n"
        "  If this is not the uv-managed executable, move ~/.local/bin (or %%USERPROFILE%%\\.local\\bin)\n"
        "  earlier in PATH or remove the legacy binary. Then restart your shell and run `algokit --version`.\n",
        active_path,
        current_binary_path,
        all_paths,
    )
