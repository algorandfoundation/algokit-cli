import logging

import click

logger = logging.getLogger(__name__)


@click.command(name="transfer")
@click.option("--sender", "-s", help="Alias of the sender account")
@click.option("--receiver", "-r", help="Alias address or NFD poiting to an account that will receive the asset(s)")
@click.option("--asset", "-id", help="ASA asset id to transfer")
@click.option("--amount", "-a", help="Amount to transfer")
@click.option("--whole-units", help="Unit the provided amount is specified as.")
@click.option("--network", "-n", help="Network where the transfer will be executed localnet|testnet|mainnet")
def transfer(  # noqa: PLR0913
    # *, if we are using booleans
    sender: str,
    receiver: str,
    asset: str,
    amount: str,
    smallest_unit: str,
    network: str,
) -> None:
    logger.info(
        f"sender {sender} receiver {receiver} asset {asset} amount {amount} smunit {smallest_unit} network {network}"
    )
