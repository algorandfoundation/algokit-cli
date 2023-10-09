import logging
import os
import typing as t
from pathlib import Path

import click
from algosdk.mnemonic import from_private_key

from algokit.core import proc
from algokit.core.conf import ALGOKIT_CONFIG
from algokit.core.deploy import load_deploy_config, load_env_files, parse_command, resolve_command
from algokit.core.tasks.wallet import get_alias

logger = logging.getLogger(__name__)


def _ensure_aliases(
    config_env: dict[str, str],
    deployer_alias: str | None = None,
    dispenser_alias: str | None = None,
) -> None:
    """
    Ensures that the required aliases for the deployer and dispenser are provided and valid and
    injects their mnemonics into env vars config.

    Args:
        config_env (dict[str, str]): A dictionary containing the environment variables.
        deployer_alias (str | None, optional): The alias for the deployer. Defaults to None.
        dispenser_alias (str | None, optional): The alias for the dispenser. Defaults to None.

    Raises:
        click.ClickException: If the alias or private key is missing.

    Returns:
        None
    """

    for key, alias in [("DEPLOYER_MNEMONIC", deployer_alias), ("DISPENSER_MNEMONIC", dispenser_alias)]:
        if not alias:
            continue

        alias_data = get_alias(alias)
        if not alias_data:
            raise click.ClickException(f"Error: missing {alias} alias")
        if not alias_data.private_key:
            raise click.ClickException(f"Error: missing private key for {alias} alias")
        config_env[key] = from_private_key(alias_data.private_key)  # type: ignore[no-untyped-call]
        logger.debug(f"Loaded {alias} alias mnemonic as {key} environment variable")


def _ensure_environment_secrets(
    config_env: dict[str, str],
    environment_secrets: list[str],
    *,
    skip_mnemonics_prompts: bool,
) -> None:
    """
    Ensures that the required environment variables are present in the `config_env` dictionary.
    If any of the environment variables are missing, it prompts the user to enter the missing variable.

    Args:
        config_env (dict[str, str]): A dictionary containing the current environment variables.
        environment_secrets (list[str]): A list of strings representing the required environment variables.
        skip_mnemonics_prompts (bool): A boolean indicating whether to skip prompting the user for missing variables.

    Raises:
        click.ClickException: If a required environment variable is missing and `skip_mnemonics_prompts` is True.

    Returns:
        None. The function modifies the `config_env` dictionary in-place.
    """

    for key in environment_secrets:
        if not config_env.get(key):
            if skip_mnemonics_prompts:
                raise click.ClickException(f"Error: missing {key} environment variable")
            config_env[key] = click.prompt(key, hide_input=True)


class CommandParamType(click.types.StringParamType):
    name = "command"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None  # noqa: ANN401
    ) -> list[str]:
        str_value = super().convert(value=value, param=param, ctx=ctx)
        try:
            return parse_command(str_value)
        except ValueError as ex:
            logger.debug(f"Failed to parse command string: {str_value}", exc_info=True)
            raise click.BadParameter(str(ex), param=param, ctx=ctx) from ex


@click.command("deploy")
@click.argument("environment_name", default=None, required=False)
@click.option(
    "--command",
    "-C",
    type=CommandParamType(),
    default=None,
    help="Custom deploy command. If not provided, will load the deploy command from .algokit.toml file.",
)
@click.option(
    "--interactive/--non-interactive",
    " /--ci",  # this aliases --non-interactive to --ci
    default=lambda: "CI" not in os.environ,
    help="Enable/disable interactive prompts. If the CI environment variable is set, defaults to non-interactive",
)
@click.option(
    "--path",
    "-P",
    type=click.Path(exists=True, readable=True, file_okay=False, resolve_path=True, path_type=Path),
    default=".",
    help="Specify the project directory. If not provided, current working directory will be used.",
)
@click.option(
    "--deployer",
    "deployer_alias",
    type=click.STRING,
    required=False,
    help=(
        "(Optional) Alias of the deployer account. Otherwise, will prompt the deployer mnemonic "
        "if specified in .algokit.toml file."
    ),
)
@click.option(
    "--dispenser",
    "dispenser_alias",
    type=click.STRING,
    required=False,
    help=(
        "(Optional) Alias of the dispenser account. Otherwise, will prompt the dispenser mnemonic "
        "if specified in .algokit.toml file."
    ),
)
def deploy_command(  # noqa: PLR0913
    *,
    environment_name: str | None,
    command: list[str] | None,
    interactive: bool,
    path: Path,
    deployer_alias: str | None,
    dispenser_alias: str | None,
) -> None:
    """Deploy smart contracts from AlgoKit compliant repository."""
    logger.debug(f"Deploying from project directory: {path}")
    logger.debug("Loading deploy command from project config")
    config = load_deploy_config(name=environment_name, project_dir=path)
    if command:
        config.command = command
    elif not config.command:
        if environment_name is None:
            msg = f"No generic deploy command specified in '{ALGOKIT_CONFIG}' file."
        else:
            msg = (
                f"Deploy command for '{environment_name}' is not specified in '{ALGOKIT_CONFIG}' file, "
                "and no generic command."
            )
        raise click.ClickException(msg)
    resolved_command = resolve_command(config.command)
    logger.info(f"Using deploy command: {' '.join(resolved_command)}")
    # TODO: [future-note] do we want to walk up for env/config?
    logger.info("Loading deployment environment variables...")
    config_dotenv = load_env_files(environment_name, path)
    # environment variables take precedence over those in .env* files
    config_env = {**{k: v for k, v in config_dotenv.items() if v is not None}, **os.environ}
    _ensure_aliases(config_env, deployer_alias=deployer_alias, dispenser_alias=dispenser_alias)

    if config.environment_secrets:
        _ensure_environment_secrets(
            config_env,
            config.environment_secrets,
            skip_mnemonics_prompts=not interactive,
        )
    logger.info("Deploying smart contracts from AlgoKit compliant repository 🚀")
    try:
        result = proc.run(resolved_command, cwd=path, env=config_env, stdout_log_level=logging.INFO)
    except FileNotFoundError as ex:
        raise click.ClickException(f"Failed to execute deploy command, '{resolved_command[0]}' wasn't found") from ex
    except PermissionError as ex:
        raise click.ClickException(
            f"Failed to execute deploy command '{resolved_command[0]}', permission denied"
        ) from ex
    else:
        if result.exit_code != 0:
            raise click.ClickException(f"Deployment command exited with error code = {result.exit_code}")
