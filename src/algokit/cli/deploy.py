import logging
import os
import shlex
import typing as t
from pathlib import Path

import algokit_utils
import click

from algokit.core import proc
from algokit.core.deploy import load_deploy_command, load_deploy_config
from algokit.core.utils import isolate_environ_changes

logger = logging.getLogger(__name__)

DEPLOYER_KEY = "DEPLOYER_MNEMONIC"
DISPENSER_KEY = "DISPENSER_MNEMONIC"


def _validate_mnemonic(value: str, *, key: str | None = None) -> str:
    # TODO: add test for this
    try:
        algokit_utils.get_account_from_mnemonic(value)
    except Exception as ex:
        if key is None:
            msg = "Invalid mnemonic"
        else:
            msg = f"Invalid mnemonic for {key}"
        raise click.ClickException(msg) from ex
    else:
        return value


def ensure_mnemonics(*, skip_mnemonics_prompts: bool) -> None:
    """
    Extract environment variables, prompt user if needed.

    :param skip_mnemonics_prompts: A boolean indicating if user prompt should be skipped.
    :return: A tuple containing deployer_mnemonic and dispenser_mnemonic.
    """
    deployer_mnemonic_in_env: bool
    if deployer_mnemonic := os.getenv(DEPLOYER_KEY):
        _validate_mnemonic(deployer_mnemonic, key=DEPLOYER_KEY)
        deployer_mnemonic_in_env = True
    else:
        deployer_mnemonic_in_env = False
        if skip_mnemonics_prompts:
            raise click.ClickException(f"Error: missing {DEPLOYER_KEY} environment variable")
        os.environ[DEPLOYER_KEY] = click.prompt("deployer-mnemonic", hide_input=True, value_proc=_validate_mnemonic)

    if dispenser_mnemonic := os.getenv(DISPENSER_KEY):
        _validate_mnemonic(dispenser_mnemonic, key=DISPENSER_KEY)
    elif deployer_mnemonic_in_env:
        # don't prompt for dispenser mnemonic if deployer mnemonic was in env vars
        pass
    elif not skip_mnemonics_prompts:
        # TODO: should we _really_ always prompt for this?
        use_dispenser = click.confirm("Do you want to use a dispenser account?", default=False)
        if use_dispenser:
            os.environ[DISPENSER_KEY] = click.prompt(
                "dispenser-mnemonic", hide_input=True, value_proc=_validate_mnemonic
            )


def _is_localnet() -> bool:
    # TODO: have tests exercise this function
    logger.debug("Getting algod client from environment variables")
    algod_client = algokit_utils.get_algod_client()
    return algokit_utils.is_localnet(algod_client)


class CommandParamType(click.types.StringParamType):
    name = "command"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None  # noqa: ANN401
    ) -> list[str]:
        str_value = super().convert(value=value, param=param, ctx=ctx)
        try:
            return shlex.split(str_value)
        except Exception as ex:
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
def deploy_command(
    *,
    environment_name: str | None,
    command: list[str] | None,
    interactive: bool,
    path: Path,
) -> None:
    """Deploy smart contracts from AlgoKit compliant repository."""
    logger.debug(f"Deploying from project directory: {path}")
    if command is None:
        logger.debug("Loading deploy command from project config")
        command = load_deploy_command(name=environment_name, project_dir=path)
    logger.info(f"Using deploy command: {' '.join(command)}")
    with isolate_environ_changes():
        # TODO: do we want to walk up for env/config?
        logger.info("Loading deployment configuration...")
        load_deploy_config(environment_name, path)
        if not _is_localnet():
            ensure_mnemonics(skip_mnemonics_prompts=not interactive)

        logger.info("Deploying smart contracts from AlgoKit compliant repository 🚀")
        try:
            # TODO: tests should exercise env var passing
            result = proc.run(command, cwd=path, stdout_log_level=logging.INFO)
        except FileNotFoundError as ex:
            raise click.ClickException("Failed to execute deploy command, command wasn't found") from ex
        except PermissionError as ex:
            raise click.ClickException("Failed to execute deploy command, permission denied") from ex
        else:
            if result.exit_code != 0:
                raise click.ClickException(f"Deployment command exited with error code = {result.exit_code}")
