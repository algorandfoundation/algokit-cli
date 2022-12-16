import dataclasses
import logging
import os
from pathlib import Path

import click
import click.testing
from click.testing import CliRunner

from tests.utils.approvals import normalize_path


logger = logging.getLogger(__name__)


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
        if result.exc_info is Exception:
            logger.error("Click invocation error", exc_info=result.exc_info)
        output = normalize_path(result.stdout, str(cwd or prior_cwd), "{current_working_directory}")
        return ClickInvokeResult(exit_code=result.exit_code, output=output)
    finally:
        if cwd is not None:
            os.chdir(prior_cwd)
