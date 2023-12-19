import json
import logging
import os
import re
from pathlib import Path

from jsondiff import diff
from pydantic import BaseModel, Field

from algokit.core.proc import RunResult, run

logger = logging.getLogger(__name__)

TEALER_REPORTS_ROOT = Path.cwd() / ".algokit/static-analysis"
TEALER_ARTIFACTS_ROOT = TEALER_REPORTS_ROOT / "artifacts"
TEALER_SNAPSHOTS_ROOT = TEALER_REPORTS_ROOT / "snapshots"
TEALER_DOT_FILES_ROOT = TEALER_REPORTS_ROOT / "tealer"


class TealerBlock(BaseModel):
    short: str
    blocks: list[list[str]]


class TealerExecutionPath(BaseModel):
    data_type: str = Field(alias="type")
    count: int
    description: str
    check: str
    impact: str
    confidence: str
    data_help: str = Field(alias="help")
    paths: list[TealerBlock]


class TealerAnalysisReport(BaseModel):
    success: bool
    data_error: str | None = Field(alias="error")
    result: list[TealerExecutionPath]


def _extract_line(block: list[str]) -> str:
    return f"{int(block[0].split(':')[0])}-{int(block[-1].split(':')[0])}"


def _extract_lines(block: list[list[str]]) -> str:
    return "->".join([_extract_line(b) for b in block])


def generate_report_filename(file: Path) -> str:
    duplicate_files: dict[str, int] = {}
    base_filename = f"{file.parent.stem}_{file.stem}"
    duplicate_count = duplicate_files.get(base_filename, 0)
    duplicate_files[base_filename] = duplicate_count + 1
    return f"{base_filename}_{duplicate_count}.json" if duplicate_count else f"{base_filename}.json"


def load_tealer_report(file_path: str) -> TealerAnalysisReport:
    """
    Load and parse the tealer report from the specified file path.

    Args:
        file_path (str): The path to the tealer report file.

    Returns:
        TealerAnalysisReport: Parsed tealer analysis report.
    """
    with Path(file_path).open() as file:
        data = json.load(file)
    return TealerAnalysisReport(**data)


def generate_tealer_command(cur_file: Path, report_output_path: Path, detectors_to_exclude: list[str]) -> list[str]:
    """
    Generate the tealer command for analyzing TEAL programs.

    Args:
        cur_file (Path): The current file to be analyzed.
        report_output_path (Path): The path to the report output.
        detectors_to_exclude (list[str]): List of detectors to be excluded.

    Returns:
        list[str]: The generated tealer command.
    """

    command = [
        "pipx",
        "run",
        "--spec",
        "git+https://github.com/algorandfoundation/tealer.git@py3.12",
        "tealer",
        "--json",
        str(report_output_path),
        "detect",
        "--contracts",
        str(cur_file),
    ]
    if detectors_to_exclude:
        excluded_detectors = ", ".join(detectors_to_exclude)
        command.extend(["--exclude", excluded_detectors])
    return command


def run_tealer(command: list[str]) -> RunResult:
    """
    Run the tealer command and return the result.

    Args:
        command (list[str]): The command to be executed.

    Returns:
        RunResult: The result of running the tealer command.
    """

    return run(
        command,
        cwd=Path.cwd(),
        env={
            "TEALER_ROOT_OUTPUT_DIR": str(TEALER_DOT_FILES_ROOT),
            **os.environ,
        },
    )


def has_baseline_diff(*, cur_file: Path, report_output_path: Path, old_report: TealerAnalysisReport) -> bool:
    """
    Handle the difference between the old and new reports for baseline comparison.

    Args:
        cur_file (Path): The current file being analyzed.
        report_output_path (Path): The path to the report output.
        old_report (TealerAnalysisReport): The old report for comparison.
    Returns:
        None
    """

    new_report = load_tealer_report(str(report_output_path))
    baseline_diff = diff(old_report.model_dump(by_alias=True), new_report.model_dump(by_alias=True))
    if baseline_diff:
        logger.error(f"Diff detected in {cur_file}! Please check the content of " f"{report_output_path}.")

        return True

    return False


def generate_table_rows(reports: dict) -> dict[Path, list[list[str]]]:
    """
    Generate table rows from the reports dictionary.

    Args:
        reports (dict): A dictionary containing the reports.

    Returns:
        dict[Path, list[list[str]]]: A dictionary containing the table rows.
    """

    # Initialize an empty dictionary to store table rows.
    table_data: dict[Path, list[list[str]]] = {}

    # Iterate through each report in the reports dictionary.
    for report_path, _ in reports.items():
        report = load_tealer_report(report_path)
        relative_path = Path(report_path).relative_to(Path.cwd())

        # Process each item in the report's result.
        for item in report.result:
            if item.count == 0:
                continue

            check_type = item.check
            impact_level = item.impact
            detailed_description = item.description + " " + item.data_help

            # Extract URL from the description, if present.
            found_url = re.search(r"(?P<url>https?://[^\s]+)", detailed_description)
            description_with_url = found_url.group("url") if found_url else detailed_description

            # Compile a list of paths or mark as 'N/A' if none.
            path_details = ",\n".join(_extract_lines(block.blocks) for block in item.paths) or "N/A"

            # Add the compiled data to the table_data dictionary.
            if relative_path not in table_data:
                table_data[relative_path] = []
            table_data[relative_path].append([check_type, impact_level, description_with_url, path_details])

    return table_data
