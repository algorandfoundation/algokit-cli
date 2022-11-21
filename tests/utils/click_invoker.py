import dataclasses
from pathlib import Path

from click.testing import CliRunner


@dataclasses.dataclass
class ClickInvokeResult:
    exit_code: int
    output: str


def invoke(args: str, *, verbose: bool = True, force_color_flag: bool | None = False) -> ClickInvokeResult:
    from algokit.cli import algokit

    runner = CliRunner()
    cwd = Path.cwd()
    flags = []
    if verbose:
        flags.append("-v")
    if force_color_flag is True:
        flags.append("--color")
    elif force_color_flag is False:
        flags.append("--no-color")
    cmd_str = " ".join([*flags, args])
    result = runner.invoke(algokit, cmd_str)
    output = result.stdout.replace(str(cwd), "{current_working_directory}")
    return ClickInvokeResult(exit_code=result.exit_code, output=output)
