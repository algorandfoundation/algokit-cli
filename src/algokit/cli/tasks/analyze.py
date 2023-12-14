import json
import logging
from pathlib import Path

import click

from algokit.cli.common.utils import MutuallyExclusiveOption
from algokit.core.tasks.analyze import (
    TEALER_ARTIFACTS_ROOT,
    TEALER_DOT_FILES_ROOT,
    TEALER_REPORTS_ROOT,
    generate_filename,
    generate_table_rows,
    generate_tealer_command,
    handle_baseline_diff,
    load_tealer_report,
    run_tealer,
)

logger = logging.getLogger(__name__)


def prepare_artifact_folders(output_dir: Path | None) -> None:
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    TEALER_REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    TEALER_ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)
    TEALER_DOT_FILES_ROOT.mkdir(parents=True, exist_ok=True)


def display_analysis_summary(analysis_results: dict):
    impact_frequency = {}
    for file_path, result_rows in analysis_results.items():
        click.echo(f"\nFile: {file_path}\n")
        for result in result_rows:
            click.echo(
                f"Detector: {result[0]}\n"
                f"Impact: {result[1]}\n"
                f"Details: {result[2]}\n"
                f"Execution Paths (#Lines):\n{result[3]}\n"
            )
            impact_frequency[result[1]] = impact_frequency.get(result[1], 0) + 1
    # print summary by impact label
    click.echo("\nTotal issues:")
    for impact, frequency in impact_frequency.items():
        click.echo(f"{impact}: {frequency}")

    click.echo(f"Finished analyzing {len(analysis_results)} files.")


@click.command(
    name="analyze",
    help="Analyze TEAL programs for common vulnerabilities with AlgoKit Tealer integration.",
)
@click.option(
    "--file",
    "-f",
    "files",
    multiple=True,
    cls=MutuallyExclusiveOption,
    not_required_if=["directory", "recursive"],
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the TEAL file to analyze. Supports multiple files in a single run.",
)
@click.option(
    "--directory",
    "-d",
    cls=MutuallyExclusiveOption,
    not_required_if=["file"],
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to a directory containing the TEAL files. Recursively search for all TEAL files within.",
)
@click.option(
    "--recursive",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    not_required_if=["file"],
    help="Recursively search for all TEAL files within the provided directory.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force verification without the disclaimer confirmation prompt.",
)
@click.option(
    "--baseline",
    is_flag=True,
    help=(
        "Exit with a non-zero code if any diffs are identified between the current "
        "and baseline reports. By default baseline reports are stored in the "
        ".algokit/static-analysis/artifacts folder. Alternatively, you can specify a "
        "custom path using the --output option to compare against."
    ),
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=False,
    default=None,
    type=click.Path(dir_okay=True, file_okay=False, resolve_path=True, path_type=Path),
    help="Directory path where to store the results of the static analysis.",
)
@click.option(
    "--exclude",
    "detectors_to_exclude",
    multiple=True,
    default=[],
    type=click.STRING,
    help="Exclude specific vulnerabilities from the analysis. Supports multiple exclusions in a single run.",
)
@click.option(
    "--diff",
    "show_diff",
    is_flag=True,
    help="Show the diff between the current and baseline reports.",
)
def analyze(  # noqa: PLR0913
    *,
    files: list[Path],
    directory: Path | None,
    recursive: bool,
    force: bool,
    baseline: bool,
    output_path: Path | None,
    detectors_to_exclude: list[str],
    show_diff: bool,
) -> None:
    """
    Analyze the TEAL programs for common vulnerabilities.

    Args:
        files (list[Path]): The files to analyze.
        directory (Path | None): The directory containing the TEAL files.
        recursive (bool): Whether to recursively search for all TEAL files within the provided directory.
        force (bool): Whether to force verification without the disclaimer confirmation prompt.
        baseline (bool): Whether to exit with a non-zero code if any diffs are
        identified between the current and baseline reports.
        output_path (Path | None): The directory path where to store the results of the static analysis.
        detectors_to_exclude (list[str]): The vulnerabilities to exclude from the analysis.
        show_diff (bool): Whether to show the diff between the current and baseline reports.
    """

    prepare_artifact_folders(output_path)

    input_files = sorted(set(files))
    detectors_to_exclude = sorted(set(detectors_to_exclude))

    if not force:
        click.confirm(
            "Standard disclaimer: This tool provides suggestions for improving "
            "your TEAL programs, but it does not guarantee their correctness "
            "or security. Do you understand?",
            abort=True,
        )

    if directory:
        pattern = "**/*.teal" if recursive else "*.teal"
        input_files.extend(sorted(directory.glob(pattern)))

    duplicate_files = {}
    reports = {}
    for cur_file in input_files:
        file = cur_file.resolve()
        filename = generate_filename(file, duplicate_files)

        report_output_root = output_path or TEALER_REPORTS_ROOT
        report_output_path = report_output_root / filename

        command = generate_tealer_command(cur_file, report_output_path, detectors_to_exclude)

        old_report = load_tealer_report(str(report_output_path)) if report_output_path.exists() and baseline else None

        result = run_tealer(command)

        if baseline and old_report:
            handle_baseline_diff(
                cur_file=cur_file, report_output_path=report_output_path, old_report=old_report, show_diff=show_diff
            )

        reports[str(report_output_path.absolute())] = json.load(report_output_path.open())

        if result.exit_code != 0:
            click.echo(
                f"An error occurred while analyzing {cur_file}. Please check the logs for more information.",
                err=True,
            )
            raise click.Abort("Error while running tealer")

    table_rows = generate_table_rows(reports)

    if table_rows:
        display_analysis_summary(table_rows)
    else:
        click.echo("No issues identified.")
