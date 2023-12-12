import os
import sys
from pathlib import Path
from typing import Optional

import click

from algokit.core.proc import run


@click.command(
    name="analyze",
    help="Analyze TEAL programs for common vulnerabilities with AlgoKit Tealer integration.",
)
@click.option(
    "--file",
    "-f",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the TEAL file to analyze. Supports multiple files in a single run.",
)
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False),
    help="Path to a directory containing the TEAL files. Recursively search for all TEAL files within.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force verification without the disclaimer confirmation prompt.",
)
@click.option(
    "--baseline",
    is_flag=True,
    help="Persist a baseline file to the .algokit directory. Any failures that exist in this baseline file will be ignored on the next run.",
)
@click.option(
    "-o",
    "--output",
    "output_file_path",
    required=False,
    default=None,
    type=click.Path(dir_okay=False, file_okay=True, resolve_path=True, path_type=Path),
    help="File path where to store the results of the static analysis.",
)
def analyze(
    file: list[Path], directory: Optional[Path], force: bool, baseline: bool, output_file_path: Path | None
) -> None:
    if not force:
        click.confirm(
            "Standard disclaimer: This tool provides suggestions for improving your TEAL programs, but it does not guarantee their correctness or security. Do you understand?",
            abort=True,
        )
    files = [Path(f) for f in file]
    if directory:
        files.extend(directory.glob("**/*.teal"))
    for cur_file in files:
        command = ["poetry", "run", "tealer", "detect", "--contracts", str(cur_file)]
        if output_file_path is not None:
            command.insert(3, "--json")
            command.insert(4, str(Path.resolve(output_file_path)))

        result = run(
            command,
            env={
                "TEALER_ROOT_OUTPUT_DIR": "/Users/aorumbayev/MakerX/projects/algokit/algokit-cli/.algokit/static-analysis",
                **os.environ,
            },
        )

        if baseline:
            with open(Path(".algokit/baseline"), "a") as f:
                f.write(f"{cur_file}: {result.output}")
        else:
            click.echo("To ignore these failures in the future, run with --baseline.")

        sys.exit(result.exit_code)
