import logging

import click

from algokit.cli.tasks.assets import opt_in_command, opt_out_command
from algokit.cli.tasks.ipfs import ipfs_group
from algokit.cli.tasks.mint import mint
from algokit.cli.tasks.nfd import nfd_lookup
from algokit.cli.tasks.send_transaction import send
from algokit.cli.tasks.sign_transaction import sign
from algokit.cli.tasks.transfer import transfer
from algokit.cli.tasks.vanity_address import vanity_address
from algokit.cli.tasks.wallet import wallet

logger = logging.getLogger(__name__)


@click.group(name="task")
def task_group() -> None:
    """Collection of useful tasks to help you develop on Algorand."""


task_group.add_command(wallet)
task_group.add_command(vanity_address)
task_group.add_command(transfer)
task_group.add_command(sign)
task_group.add_command(send)
task_group.add_command(ipfs_group)
task_group.add_command(nfd_lookup)
task_group.add_command(opt_out_command)
task_group.add_command(opt_in_command)
task_group.add_command(mint)
