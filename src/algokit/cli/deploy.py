import logging
import os
from pathlib import Path

import click

from algokit.core.deploy import DEPLOY_CONFIGS, execute_deploy_command, load_deploy_command, load_deploy_config

logger = logging.getLogger(__name__)


class HiddenSecret:
    def __init__(self, secret: str = ""):
        self.secret = secret

    def __str__(self) -> str:
        return "*" * len(self.secret)


DEPLOYER_KEY = "DEPLOYER_MNEMONIC"
DISPENSER_KEY = "DISPENSER_MNEMONIC"


@click.command("deploy")
@click.argument("network", type=click.Choice(list(DEPLOY_CONFIGS)), default="localnet", required=True)
@click.option(
    "--deployer_mnemonic",
    required=True,
    default=lambda: HiddenSecret(os.environ.get(DEPLOYER_KEY, "")),
    hide_input=True,
)
@click.option(
    "--dispenser_mnemonic",
    required=False,
    prompt=True,
    default=lambda: HiddenSecret(os.environ.get(DISPENSER_KEY, "")),
    hide_input=True,
)
@click.option(
    "--custom_deploy_command",
    type=str,
    default=None,
    help="Custom deploy command. If not provided, will load the deploy command from .algokit.toml file in the current directory.",  # noqa: E501
)
def deploy_command(network: str, deployer_mnemonic: str, dispenser_mnemonic: str, custom_deploy_command: str) -> None:
    """Deploy smart contracts from AlgoKit compliant repository.
    Will load the deploy command from .algokit.toml file in the current directory.
    Will load default configuration for network using AlgoNode. To override the default configuration,
    create a .env file in the current directory and set the required environment variables prefixed with the network name (e.g. LOCALNET_ALGOD_TOKEN and etc)
    """  # noqa: E501

    # Load deploy config
    project_dir = Path.cwd()
    deploy_config = load_deploy_config(network, project_dir)

    # Inject deploy config with mnemonic
    deploy_config[DEPLOYER_KEY] = deployer_mnemonic
    deploy_config[DISPENSER_KEY] = dispenser_mnemonic

    # Load deploy command
    deploy_command = custom_deploy_command or load_deploy_command(network_name=network, project_dir=Path.cwd())

    # Execute deploy command
    logger.info("Deploying smart contracts from AlgoKit compliant repository.")
    execute_deploy_command(command=deploy_command, deploy_config=deploy_config, project_dir=project_dir)
    logger.info("Deployment completed successfully 🎉")
