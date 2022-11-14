import click


@click.group("sandbox", short_help="Manage the Algorand sandbox")
def sandbox_group():
    print("Hello I'm the sandbox command group")


@sandbox_group.command()
def restart_sandbox():
    print("Restarting the sandbox now...")
    # TODO: the thing
    print("Done!")
