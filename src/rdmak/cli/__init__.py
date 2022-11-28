import click
from rdmak.cli.goal import goal_command
from rdmak.cli.init import init_command
from rdmak.cli.sandbox import sandbox_group
from rdmak.core.conf import PACKAGE_NAME
from rdmak.core.log_handlers import color_option, verbose_option


@click.group(
    help="AlgoKit is your one-stop shop to develop applications on the Algorand blockchain.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(package_name="rdmak")
@verbose_option
@color_option
def algokit() -> None:
    pass


algokit.add_command(init_command)
algokit.add_command(sandbox_group)
algokit.add_command(goal_command)
