import dataclasses
import logging
import platform
import shutil
from pathlib import Path

import click
import dotenv

from algokit.core.conf import ALGOKIT_CONFIG, get_algokit_config

logger = logging.getLogger(__name__)


def load_env_files(name: str | None, project_dir: Path) -> dict[str, str | None]:
    """
    Load the deploy configuration for the given network.
    :param name: Network name.
    :param project_dir: Project directory path.
    """
    general_env_path = project_dir / ".env"
    result: dict[str, str | None] = {}
    if general_env_path.exists():
        result = dotenv.dotenv_values(general_env_path, verbose=True)
    if name is not None:
        specific_env_path = project_dir / f".env.{name}"
        if not specific_env_path.exists():
            raise click.ClickException(f"No such file: {specific_env_path}")
        result |= dotenv.dotenv_values(specific_env_path, verbose=True)
    return result


@dataclasses.dataclass(kw_only=True)
class DeployConfig:
    command: list[str] | None = None
    environment_secrets: list[str] | None = None


def load_deploy_config(name: str | None, project_dir: Path) -> DeployConfig:
    """
    Load the deploy command for the given network/environment from .algokit.toml file.
    :param name: Network or environment name.
    :param project_dir: Project directory path.
    :return: Deploy command.
    """

    # Load and parse the TOML configuration file
    config = get_algokit_config(project_dir)

    deploy_config = DeployConfig()

    if config is None:
        # in the case of no algokit toml file, we return the (empty) defaults
        return deploy_config

    # ensure there is at least some config under [deploy] and that it's a dict type
    # (which should implicitly exist even if only [deploy.{name}] exists)
    match deploy_table := config.get("deploy"):
        case dict():
            pass  # expected case if there is a file with deploy config
        case None:
            return deploy_config  # file has no deploy config, we return with (empty) defaults
        case _:
            raise click.ClickException(f"Bad data for deploy in '{ALGOKIT_CONFIG}' file: {deploy_table}")

    assert isinstance(deploy_table, dict)  # because mypy is not all-knowing

    for tbl in [deploy_table, deploy_table.get(name)]:
        match tbl:
            case {"command": str(command)}:
                try:
                    deploy_config.command = parse_command(command)
                except ValueError as ex:
                    logger.debug(f"Failed to parse command string: {command}", exc_info=True)
                    raise click.ClickException(f"Failed to parse command '{command}': {ex}") from ex
            case {"command": list(command_parts)}:
                deploy_config.command = [str(x) for x in command_parts]
            case {"command": bad_data}:
                raise click.ClickException(f"Invalid data provided under 'command' key: {bad_data}")
        match tbl:
            case {"environment_secrets": list(env_names)}:
                deploy_config.environment_secrets = [str(x) for x in env_names]
            case {"environment_secrets": bad_data}:
                raise click.ClickException(f"Invalid data provided under 'environment_secrets' key: {bad_data}")

    return deploy_config


def parse_command(command: str) -> list[str]:
    if platform.system() == "Windows":
        import mslex

        return mslex.split(command)
    else:
        import shlex

        return shlex.split(command)


def resolve_command(command: list[str]) -> list[str]:
    cmd, *args = command
    # if the command has any path separators or such, don't try and resolve
    if Path(cmd).name != cmd:
        return command
    resolved_cmd = shutil.which(cmd)
    if not resolved_cmd:
        raise click.ClickException(f"Failed to resolve deploy command, '{cmd}' wasn't found")
    return [resolved_cmd, *args]
