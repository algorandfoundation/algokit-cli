import click


@click.command("example")
def example_command() -> None:
    """Example initialization subcommand."""
    click.echo("This is the example init subcommand.")
