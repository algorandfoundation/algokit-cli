import click

from algokit.cli.bootstrap import bootstrap_group
from algokit.cli.completions import completions_group
from algokit.cli.config import config_group
from algokit.cli.doctor import doctor_command
from algokit.cli.explore import explore_command
from algokit.cli.goal import goal_command
from algokit.cli.init import init_command
from algokit.cli.localnet import localnet_group
from algokit.core.conf import PACKAGE_NAME
from algokit.core.log_handlers import color_option, verbose_option
from algokit.core.version_prompt import do_version_prompt, skip_version_check_option


@click.group(
    help="AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(package_name=PACKAGE_NAME)
@verbose_option
@color_option
@skip_version_check_option
def algokit(*, skip_version_check: bool) -> None:
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
