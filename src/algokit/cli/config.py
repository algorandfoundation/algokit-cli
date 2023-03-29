import click

from algokit.core.version_prompt import version_prompt_configuration_command


@click.group("config", short_help="Configure AlgoKit settings.")
def config_group() -> None:
    """Configure settings used by AlgoKit"""


config_group.add_command(version_prompt_configuration_command)
