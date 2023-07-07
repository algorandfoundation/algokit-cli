# 1. User can call algokit deploy to different networks
# 2. By default algokit cli contains configs for testnet and mainnet
# 3. User can overwrite them by creating a config file in the project root
import logging
import shlex
from pathlib import Path

import click
from dotenv import load_dotenv

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config

logger = logging.getLogger(__name__)


def load_deploy_config(name: str | None, project_dir: Path) -> None:
    """
    Load the deploy configuration for the given network.
    :param name: Network name.
    :param project_dir: Project directory path.
    """
    general_env_path = project_dir / ".env"
    if general_env_path.exists():
        # TODO: do we really want to override here?
        load_dotenv(general_env_path, verbose=True, override=True)
    if name is not None:
        specific_env_path = project_dir / f".env.{name}"
        if specific_env_path.exists():
            # TODO: do we really want to override here?
            load_dotenv(specific_env_path, verbose=True, override=True)
        else:
            raise click.ClickException(f"No such file: {specific_env_path}")


def load_deploy_command(name: str | None, project_dir: Path) -> list[str]:
    """
    Load the deploy command for the given network/environment from .algokit.toml file.
    :param name: Network or environment name.
    :param project_dir: Project directory path.
    :return: Deploy command.
    """

    # Load and parse the TOML configuration file
    config = get_algokit_config(project_dir)

    if not config:
        raise click.ClickException(
            f"Couldn't load {ALGOKIT_CONFIG} file. Ensure deploy command is specified, either via "
            f"--command or inside {ALGOKIT_CONFIG} file."
        )

    match deploy_table := config.get("deploy"):
        case None:
            raise click.ClickException(f"No deployment commands specified in '{ALGOKIT_CONFIG}' file")
        case dict():
            pass
        case _:
            raise click.ClickException(f"Bad data for deploy in '{ALGOKIT_CONFIG}' file: {deploy_table}")
    assert isinstance(deploy_table, dict)

    for tbl in [deploy_table.get(name), deploy_table]:
        match tbl:
            case {"command": str(command)}:
                try:
                    return shlex.split(command)
                except Exception as ex:
                    raise click.ClickException(f"Failed to parse command '{command}': {ex}") from ex
            case {"command": list(command_parts)}:
                return [str(x) for x in command_parts]

    if name is None:
        msg = f"No generic deploy command specified in '{ALGOKIT_CONFIG}' file."
    else:
        msg = f"Deploy command for '{name}' is not specified in '{ALGOKIT_CONFIG}' file, and no generic command."
    raise click.ClickException(msg)
