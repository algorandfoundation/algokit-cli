import click

from algokit.cli.bootstrap import bootstrap_group
from algokit.cli.completions import completions_group
from algokit.cli.config import config_group
from algokit.cli.deploy import deploy_command
from algokit.cli.dispenser import dispenser_group
from algokit.cli.doctor import doctor_command
from algokit.cli.explore import explore_command
from algokit.cli.generate import generate_group
from algokit.cli.goal import goal_command
from algokit.cli.init import init_command
from algokit.cli.localnet import localnet_group
from algokit.core.conf import PACKAGE_NAME
from algokit.core.log_handlers import color_option, verbose_option
from algokit.core.version_prompt import do_version_prompt, skip_version_check_option


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 120,
    },
)
@click.version_option(package_name=PACKAGE_NAME)
@verbose_option
@color_option
@skip_version_check_option
def algokit(*, skip_version_check: bool) -> None:
    """
    AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.

    If you are getting started, please see the quick start tutorial: https://bit.ly/algokit-intro-tutorial.
    """
    if not skip_version_check:
        do_version_prompt()


algokit.add_command(bootstrap_group)
algokit.add_command(completions_group)
algokit.add_command(config_group)
algokit.add_command(doctor_command)
algokit.add_command(explore_command)
algokit.add_command(goal_command)
algokit.add_command(init_command)
algokit.add_command(localnet_group)
algokit.add_command(generate_group)
algokit.add_command(deploy_command)
algokit.add_command(dispenser_group)
