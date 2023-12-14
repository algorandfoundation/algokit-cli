import json
import logging
import os
import re
from pathlib import Path

from jsondiff import diff
from pydantic import BaseModel, Field

from algokit.core.proc import RunResult, run

logger = logging.getLogger(__name__)

TEALER_REPORTS_ROOT = Path.cwd() / Path(".algokit/static-analysis")
TEALER_ARTIFACTS_ROOT = TEALER_REPORTS_ROOT / "artifacts"
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


def load_tealer_report(file_path: str) -> TealerAnalysisReport:
    with Path(file_path).open() as file:
        data = json.load(file)
    return TealerAnalysisReport(**data)


def extract_line(block: list[str]) -> str:
    return f"{int(block[0].split(':')[0])}-{int(block[-1].split(':')[0])}"


def extract_lines(block: list[list[str]]) -> str:
    return "->".join([extract_line(b) for b in block])


def generate_filename(file: Path, duplicate_files: dict) -> str:
    filename = f"{file.parent.stem}_{file.stem}"
    if filename in duplicate_files:
        duplicate_files[filename] += 1
        filename = f"{filename}_{duplicate_files[filename]}.json"
    else:
        duplicate_files[filename] = 0
        filename = f"{filename}.json"
    return filename


def generate_tealer_command(cur_file: Path, report_output_path: Path, detectors_to_exclude: list[str]) -> list[str]:
    command = [
        "poetry",
        "run",
        "tealer",
        "--json",
        str(report_output_path),
        "detect",
        "--contracts",
        str(cur_file),
    ]
    if detectors_to_exclude:
        for detector in detectors_to_exclude:
            command.extend(["--exclude", detector])
    return command


def run_tealer(command: list[str]) -> RunResult:
    return run(
        command,
        cwd=Path.cwd(),
        env={
            "TEALER_ROOT_OUTPUT_DIR": str(TEALER_DOT_FILES_ROOT),
            **os.environ,
        },
    )


def handle_baseline_diff(
    *, cur_file: Path, report_output_path: Path, old_report: TealerAnalysisReport, show_diff: bool
):
    new_report = load_tealer_report(str(report_output_path))
    baseline_diff = diff(old_report.model_dump(), new_report.model_dump())
    if baseline_diff:
        logger.info(f"Diff detected in {cur_file}! Please check the content of " f"{report_output_path}.")
        if show_diff:
            logger.error(baseline_diff)
            logger.error("Diff detected in the report.")
        else:
            logger.info("To output the diff use --diff option.")


def generate_table_rows(reports: dict) -> dict:
    table_rows = {}
    for report_path, _ in reports.items():
        report = load_tealer_report(report_path)
        file_path = Path(report_path).relative_to(Path.cwd())
        for path in report.result:
            if path.count == 0:
                continue
            check_type = path.check
            impact = path.impact
            description = path.description + " " + path.data_help
            url = re.search(r"(?P<url>https?://[^\s]+)", description)
            description_and_help_text = url.group("url") if url else description
            paths = ",\n".join(extract_lines(block.blocks) for block in path.paths) or "N/A"
            if file_path not in table_rows:
                table_rows[file_path] = []
            table_rows[file_path].append([check_type, impact, description_and_help_text, paths])
    return table_rows
