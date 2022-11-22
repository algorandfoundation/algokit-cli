import json
import os
from pathlib import Path

import pytest
from approvaltests import Reporter, reporters, set_default_reporter  # type: ignore
from approvaltests.reporters.generic_diff_reporter_config import create_config  # type: ignore
from approvaltests.reporters.generic_diff_reporter_factory import GenericDiffReporter  # type: ignore
from pytest_mock import MockerFixture
from utils.app_dir_mock import AppDirs, tmp_app_dir
from utils.exec_mock import ExecMock


@pytest.fixture
def exec_mock(mocker: MockerFixture) -> ExecMock:
    exec_mock = ExecMock()
    # add a default for docker compose version
    exec_mock.set_output(["docker", "compose", "version", "--format", "json"], [json.dumps({"version": "v2.5.0"})])
    mocker.patch("algokit.core.exec.Popen").side_effect = exec_mock.popen
    return exec_mock


@pytest.fixture
def app_dir_mock(mocker: MockerFixture, tmp_path: Path) -> AppDirs:
    return tmp_app_dir(mocker, tmp_path)


if os.getenv("CI"):
    set_default_reporter(reporters.PythonNativeReporter())
else:

    default_reporters: list[Reporter] = (
        [
            GenericDiffReporter(
                create_config(
                    [
                        os.getenv("APPROVAL_REPORTER"),
                        os.getenv("APPROVAL_REPORTER_PATH"),
                        os.getenv("APPROVAL_REPORTER_ARGS", "").split(),
                    ]
                )
            )
        ]
        if os.getenv("APPROVAL_REPORTER")
        else []
    )
    default_reporters += [
        GenericDiffReporter(create_config(["kdiff3", "/usr/bin/kdiff3"])),
        GenericDiffReporter(create_config(["DiffMerge", "/Applications/DiffMerge.app/Contents/MacOS/DiffMerge"])),
        GenericDiffReporter(create_config(["TortoiseGit", "{ProgramFiles}\\TortoiseGit\\bin\\TortoiseGitMerge.exe"])),
        GenericDiffReporter(create_config(["VSCodeInsiders", "code-insiders", ["-d"]])),
        reporters.ReportWithBeyondCompare(),
        reporters.ReportWithWinMerge(),
        reporters.ReportWithVSCode(),
        reporters.PythonNativeReporter(),
    ]
    set_default_reporter(reporters.FirstWorkingReporter(*default_reporters))
