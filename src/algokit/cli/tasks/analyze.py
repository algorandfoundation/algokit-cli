import json
import logging
import re
from pathlib import Path

import click

from algokit.core.tasks.analyze import (
    TEALER_SNAPSHOTS_ROOT,
    ensure_tealer_installed,
    generate_report_filename,
    generate_summaries,
    generate_tealer_command,
    has_baseline_diff,
    load_tealer_report,
    prepare_artifacts_folders,
    run_tealer,
)
from algokit.core.utils import run_with_animation

logger = logging.getLogger(__name__)


def display_analysis_summary(analysis_results: dict) -> None:
    """
    Display the summary of the analysis results.

    Args:
        analysis_results (dict): Dictionary containing analysis results.
    """
    impact_frequency: dict = {}
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
        click.secho(f"{impact}: {frequency}", fg="yellow")


def has_template_vars(path: Path) -> bool:
    """
    Check if the file contains template variables.

    Args:
        path (Path): The file path to check.

    Returns:
        bool: True if template variables are found, False otherwise.
    """
    content = path.read_text()
    return bool(re.search(r"^(?!.*//.*TMPL_).*TMPL_.*", content, flags=re.MULTILINE))


def get_input_files(*, input_paths: tuple[Path], recursive: bool) -> list[Path]:
    """
    Get input files based on the input paths and recursive flag.

    Args:
        input_paths (tuple[Path]): Tuple of input paths.
        recursive (bool): Flag to indicate recursive search.

    Returns:
        list[Path]: List of input files.
    """

    input_files = []
    for input_path in input_paths:
        if input_path.is_dir():
            pattern = "**/*.teal" if recursive else "*.teal"
            input_files.extend(sorted(input_path.glob(pattern)))
        else:
            if recursive:
                click.secho(
                    f"Warning: Ignoring recursive flag for {input_path} as it is not a directory.\n",
                    fg="yellow",
                )
            input_files.append(input_path)
    return sorted(set(input_files))


@click.command(
    name="analyze",
    help=(
        "Analyze TEAL programs for common vulnerabilities using Tealer. "
        "This task uses a third party tool to suggest improvements for your TEAL programs, "
        "but remember to always test your smart contracts code, follow modern software engineering practices "
        "and use the guidelines for smart contract development. "
        "This should not be used as a substitute for an actual audit. "
        "For full list of available detectors, please refer to https://github.com/crytic/tealer?tab=readme-ov-file#detectors"
    ),
)
@click.argument(
    "input_paths",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=True, file_okay=True, path_type=Path),
    required=True,
)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    help="Recursively search for all TEAL files within the provided directory.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force verification without the disclaimer confirmation prompt.",
)
@click.option(
    "--diff",
    "diff_only",
    is_flag=True,
    help=(
        "Exit with a non-zero code if differences are found between current "
        "and last reports. Reports are generated each run, but with this flag "
        "execution fails if the current report doesn't match "
        "the last report. Reports are stored in the "
        ".algokit/static-analysis/snapshots folder by default. Use --output for a "
        "custom path."
    ),
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=False,
    default=None,
    type=click.Path(dir_okay=True, file_okay=False, resolve_path=True, path_type=Path),
    help=(
        "Directory path where to store the results of the static analysis. "
        "Defaults to .algokit/static-analysis/snapshots."
    ),
)
@click.option(
    "-e",
    "--exclude",
    "detectors_to_exclude",
    multiple=True,
    default=[],
    type=click.STRING,
    help="Exclude specific vulnerabilities from the analysis. Supports multiple exclusions in a single run.",
)
def analyze(  # noqa: PLR0913, C901
    *,
    input_paths: tuple[Path],
    recursive: bool,
    force: bool,
    diff_only: bool,
    output_path: Path | None,
    detectors_to_exclude: list[str],
) -> None:
    """
    Analyze TEAL programs for common vulnerabilities using Tealer.
    """

    # Install tealer if needed
    ensure_tealer_installed()

    detectors_to_exclude = sorted(set(detectors_to_exclude))
    input_files = get_input_files(input_paths=input_paths, recursive=recursive)

    if not force:
        click.confirm(
            click.style(
                "Warning: This task uses `tealer` to suggest improvements for your TEAL programs, "
                "but remember to always test your smart contracts code, follow modern software engineering practices "
                "and use the guidelines for smart contract development. "
                "This should not be used as a substitute for an actual audit. Do you understand?",
                fg="yellow",
            ),
            default=True,
            abort=True,
        )

    reports = {}
    duplicate_files: dict[str, int] = {}
    prepare_artifacts_folders(output_path)
    total_files = len(input_files)
    for index in range(total_files):
        cur_file = input_files[index]
        file = cur_file.resolve()

        if has_template_vars(file):
            click.secho(
                f"Warning: Skipping {file} due to template variables. Substitute them before scanning.",
                err=True,
                fg="yellow",
            )
            continue

        filename = generate_report_filename(file, duplicate_files)

        # If a custom output path is provided, store the report in the specified path
        report_output_root = output_path or TEALER_SNAPSHOTS_ROOT
        report_output_path = report_output_root / filename

        command = generate_tealer_command(cur_file, report_output_path, detectors_to_exclude)
        old_report = load_tealer_report(str(report_output_path)) if report_output_path.exists() and diff_only else None
        if not old_report and diff_only:
            click.secho(
                f"Unable to provide the diff since {file} report is missing. "
                "Please run the task without the --diff flag first.",
                err=True,
                fg="red",
            )
            raise click.exceptions.Exit(1)

        try:
            run_with_animation(run_tealer, f"Analyzing {index + 1} out of {total_files} files", command)

            if diff_only and old_report:
                has_diff = has_baseline_diff(
                    cur_file=cur_file, report_output_path=report_output_path, old_report=old_report
                )
                if has_diff:
                    raise click.exceptions.Exit(1)

            reports[str(report_output_path.absolute())] = json.load(report_output_path.open())
        except Exception as e:
            if diff_only and old_report:
                report_output_path.write_text(json.dumps(old_report.model_dump(by_alias=True), indent=2))

            if isinstance(e, click.exceptions.Exit):
                raise e

            click.secho(
                f"An error occurred while analyzing {cur_file}. "
                "Please make sure the files supplied are valid TEAL code before trying again.",
                err=True,
                fg="red",
            )
            raise click.Abort("Error while running tealer") from e

    summaries = generate_summaries(reports, detectors_to_exclude=detectors_to_exclude)

    if summaries and not diff_only:
        display_analysis_summary(summaries)
        click.echo(f"Finished analyzing {total_files} files.")
        raise click.exceptions.Exit(1)
