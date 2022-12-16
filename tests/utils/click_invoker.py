import dataclasses
import os
import re
from pathlib import Path

import click
import click.testing
from click.testing import CliRunner


@dataclasses.dataclass
class ClickInvokeResult:
    exit_code: int
    output: str


def invoke(
    args: str,
    *,
    cwd: Path | None = None,
    env: dict[str, str | None] | None = None,
) -> ClickInvokeResult:
    from algokit.cli import algokit

    runner = CliRunner()
    prior_cwd = Path.cwd()
    assert isinstance(algokit, click.BaseCommand)
    if cwd is not None:
        os.chdir(cwd)
    try:
        result = runner.invoke(algokit, f"-v --no-color {args}", env=env)  # type: ignore
        output = re.sub(
            r"{current_working_directory}\S+",
            lambda m: m[0].replace("\\", "/"),
            result.stdout.replace(str(cwd or prior_cwd), "{current_working_directory}").replace(
                str(cwd or prior_cwd).replace("\\", "/"), "{current_working_directory}"
            ),
        )
        return ClickInvokeResult(exit_code=result.exit_code, output=output)
    finally:
        if cwd is not None:
            os.chdir(prior_cwd)
