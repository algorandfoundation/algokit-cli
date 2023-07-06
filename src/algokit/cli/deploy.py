import logging
import os
from pathlib import Path

import algokit_utils
import click

from algokit.core import proc
from algokit.core.deploy import LOCALNET, LOCALNET_ALIASES, MAINNET, load_deploy_command, load_deploy_config
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
    if deployer_mnemonic := os.getenv(DEPLOYER_KEY):
        _validate_mnemonic(deployer_mnemonic, key=DEPLOYER_KEY)
    else:
        if skip_mnemonics_prompts:
            raise click.ClickException(f"Error: missing {DEPLOYER_KEY} environment variable")
        os.environ[DEPLOYER_KEY] = click.prompt("deployer-mnemonic", hide_input=True, value_proc=_validate_mnemonic)

    if dispenser_mnemonic := os.getenv(DISPENSER_KEY):
        _validate_mnemonic(dispenser_mnemonic, key=DISPENSER_KEY)
    elif not skip_mnemonics_prompts:
        use_dispenser = click.confirm("Do you want to use a dispenser account?", default=False)
        if use_dispenser:
            os.environ[DISPENSER_KEY] = click.prompt(
                "dispenser-mnemonic", hide_input=True, value_proc=_validate_mnemonic
            )


def _get_network_name_from_environment() -> str:
    # TODO: have tests exercise this function
    algod_client = algokit_utils.get_algod_client()
    network_genesis = algod_client.genesis()
    match network_genesis:
        case {"network": str(network_name)}:
            return network_name
        case _:
            logger.debug(f"No network found in genesis result: {network_genesis!r}")
            raise click.ClickException("Unable to extract network name from genesis response")


@click.command("deploy")
@click.argument("network_or_environment_name", default=LOCALNET)
@click.option(
    "command",
    "--custom-deploy-command",
    type=str,
    default=None,
    help="Custom deploy command. If not provided, will load the deploy command from .algokit.toml file.",
)
@click.option(
    "skip_mnemonics_prompts",
    "--ci",
    is_flag=True,
    default=False,
    help="Skip interactive prompt for mnemonics, expects them to be set as environment variables.",
)
@click.option(
    "is_production_environment",
    "--prod",
    is_flag=True,
    default=False,
    help="Skip warning prompt for deployments to a mainnet.",
)
@click.option(
    "project_dir",
    "--project-dir",
    type=click.Path(exists=True, readable=True, file_okay=False, resolve_path=True, path_type=Path),
    default=".",
    help="Specify the project directory. If not provided, current working directory will be used.",
)
def deploy_command(
    *,
    network_or_environment_name: str,
    command: str | None,
    skip_mnemonics_prompts: bool,
    is_production_environment: bool,
    project_dir: Path,
) -> None:
    """Deploy smart contracts from AlgoKit compliant repository."""
    logger.debug(f"Deploying from project directory: {project_dir}")

    if command is None:
        command = load_deploy_command(name=network_or_environment_name, project_dir=project_dir)
    logger.info(f"Using deploy command: {command}")

    with isolate_environ_changes():
        # TODO: do we want to walk up for env/config?
        load_deploy_config(network_or_environment_name, project_dir)
        logger.info("Loaded deployment configuration.")
        logger.info("Checking deployment network...")
        network_name = _get_network_name_from_environment()
        logger.info(f"Starting deployment process for network '{network_name}'...")
        if network_name not in LOCALNET_ALIASES:
            if network_name == MAINNET and not is_production_environment:
                click.confirm(
                    "You are about to deploy to the MainNet. Are you sure you want to continue?",
                    abort=True,
                )
            ensure_mnemonics(skip_mnemonics_prompts=skip_mnemonics_prompts)

        logger.info("Deploying smart contracts from AlgoKit compliant repository 🚀")
        try:
            # TODO: tests should exercise env var passing
            result = proc.run(command.split(), cwd=project_dir, stdout_log_level=logging.INFO)
        except FileNotFoundError as ex:
            raise click.ClickException("Failed to execute deploy command, command wasn't found") from ex
        except PermissionError as ex:
            raise click.ClickException("Failed to execute deploy command, permission denied") from ex
        else:
            if result.exit_code != 0:
                raise click.ClickException(f"Deployment command exited with error code = {result.exit_code}")
