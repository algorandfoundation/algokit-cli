import dataclasses
import logging
import os
from collections.abc import Mapping
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
    exception: BaseException | None


def invoke(
    args: str,
    *,
    cwd: Path | None = None,
    skip_version_check: bool = True,
    env: Mapping[str, str | None] | None = None,
) -> ClickInvokeResult:
    from algokit.cli import algokit

    runner = CliRunner()
    prior_cwd = Path.cwd()
    assert isinstance(algokit, click.BaseCommand)
    if cwd is not None:
        os.chdir(cwd)
    try:
        test_args = "-v --no-color"
        if skip_version_check:
            test_args = f"{test_args} --skip-version-check"
        result = runner.invoke(algokit, f"{test_args} {args}", env=env)
        if result.exc_info is not None:
            logger.error("Click invocation error", exc_info=result.exc_info)
        output = normalize_path(result.stdout, str(cwd or prior_cwd), "{current_working_directory}")
        return ClickInvokeResult(exit_code=result.exit_code, output=output, exception=result.exception)
    finally:
        if cwd is not None:
            os.chdir(prior_cwd)
