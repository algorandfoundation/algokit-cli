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
        # TODO: should we _really_ always prompt for this?
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
# TODO: think about default experience here, especially with .env file that might specify network params
@click.argument("network_or_environment_name", default=LOCALNET)
@click.option(
    "--command",
    "-C",
    type=str,
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
    "--mainnet-prompt/--no-mainnet-prompt",
    default=True,
    help="Skip warning prompt for deployments to a mainnet.",
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
    network_or_environment_name: str,
    command: str | None,
    interactive: bool,
    mainnet_prompt: bool,
    path: Path,
) -> None:
    """Deploy smart contracts from AlgoKit compliant repository."""
    logger.debug(f"Deploying from project directory: {path}")

    if command is None:
        command = load_deploy_command(name=network_or_environment_name, project_dir=path)
    logger.info(f"Using deploy command: {command}")

    with isolate_environ_changes():
        # TODO: do we want to walk up for env/config?
        load_deploy_config(network_or_environment_name, path)
        logger.info("Loaded deployment configuration.")
        logger.info("Checking deployment network...")
        network_name = _get_network_name_from_environment()
        logger.info(f"Starting deployment process for network '{network_name}'...")
        if network_name not in LOCALNET_ALIASES:
            if network_name == MAINNET and mainnet_prompt:
                if not interactive:
                    raise click.ClickException(
                        "To deploy to mainnet non-interactively, --no-mainnet-prompt must also be specified"
                    )
                click.confirm(
                    "You are about to deploy to the MainNet. Are you sure you want to continue?",
                    abort=True,
                )
            ensure_mnemonics(skip_mnemonics_prompts=not interactive)

        logger.info("Deploying smart contracts from AlgoKit compliant repository 🚀")
        try:
            # TODO: tests should exercise env var passing
            result = proc.run(command.split(), cwd=path, stdout_log_level=logging.INFO)
        except FileNotFoundError as ex:
            raise click.ClickException("Failed to execute deploy command, command wasn't found") from ex
        except PermissionError as ex:
            raise click.ClickException("Failed to execute deploy command, permission denied") from ex
        else:
            if result.exit_code != 0:
                raise click.ClickException(f"Deployment command exited with error code = {result.exit_code}")
