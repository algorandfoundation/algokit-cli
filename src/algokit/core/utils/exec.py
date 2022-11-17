import subprocess
from pathlib import Path

import click


def run(
    command: str,
    working_directory: Path | None = None,
    suppress_output: bool = False,
    throw_on_error: str | None = None,
):
    click.echo(click.style(f"Running '{command}' in '{working_directory or Path.cwd()}'", fg="blue"))
    result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory)
    if not suppress_output and result.stdout.decode("utf-8").strip().__len__() > 0:
        click.echo(click.style(result.stdout.decode("utf-8"), fg="blue"))

    if throw_on_error is not None and result.returncode != 0:
        click.echo(click.style(result.stderr.decode("utf-8"), fg="red"))
        raise click.ClickException(throw_on_error)

    return result
