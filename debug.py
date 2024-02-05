"""
This script is for invoking algokit from your IDE with a dynamic set of args,
defined in args.in (which is in .gitignore)
"""

import os
import subprocess
import sys
from pathlib import Path

try:
    import click
except ImportError:
    print(  # noqa: T201
        "ERROR: Couldn't import click, make sure you've run 'poetry install' and activated the virtual environment.\n"
        "For tips on getting started with developing AlgoKit CLI itself see CONTRIBUTING.md.\n",
        file=sys.stderr,
    )
    raise

if sys.prefix == sys.base_prefix:
    click.echo(
        click.style(
            "WARNING: virtualenv not activated, this is unexpected and you probably want to activate it first",
            fg="red",
        ),
        err=True,
    )

vcs_root = Path(__file__).parent
args_file = vcs_root / "args.in"
if not args_file.exists():
    click.echo(
        click.style(
            "arg.in does not exist, creating an empty file.\n"
            "Edit this file to change what runs - each line should contain the command line arguments to algokit.\n"
            "\n",
            fg="yellow",
        ),
        err=True,
    )
    args_file.touch(exist_ok=False)
    args_file.write_text("--version")

commands_sequence = args_file.read_text().splitlines()

# change to src directory so algokit is in path
os.chdir(vcs_root / "src")
for command in commands_sequence or [""]:
    click.echo(click.style(f"> algokit -v {command}", bold=True), err=True)
    run_result = subprocess.run([sys.executable, "-m", "algokit", "-v", *command.split()], check=False)
    if run_result.returncode != 0:
        click.echo(
            click.style(
                f"command failed, return code was: {run_result.returncode}",
                bold=True,
                fg="red",
            ),
            err=True,
        )
        sys.exit(run_result.returncode)
