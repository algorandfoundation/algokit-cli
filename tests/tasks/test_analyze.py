import re
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from algokit.cli.tasks.analyze import has_template_vars
from pytest_mock import MockerFixture

from tests.tasks.conftest import DUMMY_TEAL_FILE_CONTENT
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def _format_snapshot(output: str, targets: list[str], replacement: str = "dummy") -> str:
    from algokit.core.utils import get_base_python_path

    python_base_path = get_base_python_path()
    if python_base_path is None:
        pytest.fail("Python base detection failed, this should work (even in CI)")

    output = output.replace(python_base_path, "python_base_path")

    for target in targets:
        output = output.replace(target, replacement)

    # If output contains more than one new line trim them to have at most one whitespace in between
    patterns_to_remove = [
        r"^(pipx:|DEBUG: pipx:|DEBUG: tealer).*",
        r"^(Tealer installed successfully via pipx!).*",
        r"^(DEBUG: Running 'pipx install tealer==0.1.1').*",
        r"^(Tealer not found; attempting to install it...).*",
        r"^(No such file or directory:).*",
        r"^(DEBUG: Running 'pipx --version' in '{current_working_directory}').*",
    ]

    for pattern in patterns_to_remove:
        output = re.sub(pattern, "", output, flags=re.MULTILINE)

    return re.sub(r"\n\s*\n", "\n\n", output)


def _normalize_path(path: Path) -> str:
    return str(path.absolute()).replace("\\", r"\\")


@pytest.fixture(autouse=True)
def _disable_animation(mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.utils.animate", return_value=None)


@pytest.fixture(autouse=True)
def cwd(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path, None, None]:
    cwd = tmp_path_factory.mktemp("cwd", numbered=True)

    with patch("algokit.core.tasks.analyze.TEALER_REPORTS_ROOT", return_value=cwd), patch(
        "algokit.core.tasks.analyze.TEALER_SNAPSHOTS_ROOT", return_value=cwd
    ), patch("algokit.core.tasks.analyze.TEALER_DOT_FILES_ROOT", return_value=cwd):
        yield cwd


@pytest.fixture()
def generate_report_filename_mock() -> Generator[MagicMock, None, None]:
    with patch("algokit.cli.tasks.analyze.generate_report_filename", return_value="dummy_report.json") as mock:
        yield mock


@pytest.mark.usefixtures("generate_report_filename_mock")
def test_analyze_single_file(
    cwd: Path,
) -> None:
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(DUMMY_TEAL_FILE_CONTENT)
    result = invoke(f"task analyze {_normalize_path(teal_file)} --output {_normalize_path(cwd)}", input="y\n", cwd=cwd)

    assert result.exit_code == 1
    result.output = _format_snapshot(
        result.output,
        [
            str(cwd),
        ],
    )
    verify(result.output)


def test_analyze_multiple_files(
    cwd: Path,
    generate_report_filename_mock: MagicMock,
) -> None:
    generate_report_filename_mock.side_effect = [f"dummy_{i}.teal" for i in range(5)]
    teal_folder = cwd / "dummy_contracts"
    teal_folder.mkdir()
    for i in range(5):
        teal_file = teal_folder / f"dummy_{i}.teal"
        teal_file.write_text(DUMMY_TEAL_FILE_CONTENT)
    result = invoke(
        f"task analyze {_normalize_path(teal_folder)} --output {_normalize_path(cwd)}", input="y\n", cwd=cwd
    )

    assert result.exit_code == 1
    for i in range(5):
        result.output = result.output.replace(str(teal_folder / f"dummy_{i}.teal"), f"dummy_contracts/dummy_{i}.teal")
    result.output = _format_snapshot(
        result.output,
        [
            str(cwd),
        ],
    )
    verify(result.output)


def test_analyze_multiple_files_recursive(
    cwd: Path,
    generate_report_filename_mock: MagicMock,
) -> None:
    teal_root_folder = cwd / "dummy_contracts"
    generate_report_filename_mock.side_effect = [teal_root_folder / f"subfolder_{i}/dummy.teal" for i in range(5)]

    for i in range(5):
        teal_folder = teal_root_folder / f"subfolder_{i}"
        teal_folder.mkdir(parents=True)
        teal_file = teal_folder / "dummy.teal"
        teal_file.write_text(DUMMY_TEAL_FILE_CONTENT)
    result = invoke(
        f"task analyze {_normalize_path(teal_root_folder)} --recursive --output {_normalize_path(cwd)}",
        input="y\n",
        cwd=cwd,
    )

    assert result.exit_code == 1
    for i in range(5):
        result.output = re.sub(r"^File: .*", f"File:  {i}_dummy.teal", result.output, flags=re.MULTILINE)
    result.output = _format_snapshot(
        result.output,
        [str(cwd)],
        "dummy_file.teal",
    )
    verify(result.output)


@pytest.mark.usefixtures("generate_report_filename_mock")
def test_exclude_vulnerabilities(
    cwd: Path,
) -> None:
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(DUMMY_TEAL_FILE_CONTENT)
    result = invoke(
        f"task analyze {_normalize_path(teal_file)} --exclude is-deletable "
        f"--exclude rekey-to --exclude missing-fee-check --output {_normalize_path(cwd)}",
        input="y\n",
        cwd=cwd,
    )

    assert result.exit_code == 0
    result.output = _format_snapshot(result.output, [str(cwd)])
    verify(result.output)


def test_analyze_skipping_tmpl_vars(
    cwd: Path,
) -> None:
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(
        DUMMY_TEAL_FILE_CONTENT.replace("pushint 4 // UpdateApplication", "pushint TMPL_VAR // UpdateApplication")
    )
    result = invoke(f"task analyze {_normalize_path(teal_file)}", input="y\n", cwd=cwd)

    assert result.exit_code == 0
    result.output = _format_snapshot(result.output, [str(cwd)])
    verify(result.output)


def test_analyze_commented_tmpl_vars(
    cwd: Path,
) -> None:
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(
        DUMMY_TEAL_FILE_CONTENT.replace("pushint 4 // UpdateApplication", "pushint TMPL_VAR // UpdateApplication")
    )
    assert has_template_vars(teal_file)

    teal_file.write_text(DUMMY_TEAL_FILE_CONTENT.replace("pushint 4 // UpdateApplication", "pushint 4 // TMPL_VAR"))
    assert not has_template_vars(teal_file)


def test_analyze_abort_disclaimer(
    cwd: Path,
) -> None:
    teal_file = cwd / "dummy.teal"
    teal_file.touch()
    result = invoke(f"task analyze {_normalize_path(teal_file)} --output {_normalize_path(cwd)}", input="n\n", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_analyze_error_in_tealer(
    cwd: Path,
    mocker: MockerFixture,
) -> None:
    with mocker.patch("algokit.cli.tasks.analyze.run_tealer", side_effect=Exception("dummy")):
        teal_file = cwd / "dummy.teal"
        teal_file.touch()
        result = invoke(
            f"task analyze {_normalize_path(teal_file)} --output {_normalize_path(cwd)}", input="y\n", cwd=cwd
        )

        assert result.exit_code == 1
        result.output = _format_snapshot(result.output, [str(cwd)])
        verify(result.output)


def test_analyze_diff_flag(
    cwd: Path,
) -> None:
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(DUMMY_TEAL_FILE_CONTENT)
    result = invoke(f"task analyze {_normalize_path(teal_file)} --output {_normalize_path(cwd)}", input="y\n", cwd=cwd)
    assert result.exit_code == 1

    teal_file.write_text("\n#pragma version 8\nint 1\nreturn\n")
    result = invoke(
        f"task analyze {_normalize_path(teal_file)} --diff --output {_normalize_path(cwd)}", input="y\n", cwd=cwd
    )
    assert result.exit_code == 1
    result.output = _format_snapshot(result.output, [str(cwd)])
    verify(result.output)


@pytest.mark.usefixtures("generate_report_filename_mock")
def test_analyze_diff_flag_missing_old_report(
    cwd: Path,
) -> None:
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(DUMMY_TEAL_FILE_CONTENT)
    result = invoke(
        f"task analyze {_normalize_path(teal_file)} --diff --output {_normalize_path(cwd)}", input="y\n", cwd=cwd
    )
    assert result.exit_code == 1
    result.output = _format_snapshot(result.output, [str(cwd)])
    verify(result.output)


def test_analyze_error_no_pipx(cwd: Path, mocker: MockerFixture, proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on("tealer --version")
    mocker.patch("algokit.core.utils.get_candidate_pipx_commands", return_value=[])

    teal_file = cwd / "dummy.teal"
    teal_file.touch()
    result = invoke(f"task analyze {_normalize_path(teal_file)}", input="y\n", cwd=cwd)

    assert result.exit_code == 1
    result.output = _format_snapshot(result.output, [str(cwd)])
    verify(result.output)
