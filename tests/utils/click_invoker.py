import dataclasses
from pathlib import Path

import click
import click.testing
from click.testing import CliRunner


@dataclasses.dataclass
class ClickInvokeResult:
    exit_code: int
    output: str


def invoke(args: str) -> ClickInvokeResult:
    from algokit.cli import algokit

    runner = CliRunner()
    cwd = Path.cwd()
    assert isinstance(algokit, click.BaseCommand)
    result = runner.invoke(algokit, f"-v --no-color {args}")  # type: ignore
    output = result.stdout.replace(str(cwd), "{current_working_directory}")
    return ClickInvokeResult(exit_code=result.exit_code, output=output)
