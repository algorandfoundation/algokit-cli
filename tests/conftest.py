import json
import os
import typing
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from approvaltests import Reporter, reporters, set_default_reporter  # type: ignore
from approvaltests.reporters.generic_diff_reporter_config import create_config  # type: ignore
from approvaltests.reporters.generic_diff_reporter_factory import GenericDiffReporter  # type: ignore
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import PipeInput, create_pipe_input
from prompt_toolkit.output import DummyOutput
from pytest_mock import MockerFixture
from utils.app_dir_mock import AppDirs, tmp_app_dir
from utils.proc_mock import ProcMock


@pytest.fixture(autouse=True)
def latest_version_mock(mocker: MockerFixture) -> MagicMock:
    # disable version check by default
    return mocker.patch("algokit.core.version_check._do_version_check")


@pytest.fixture
def proc_mock(mocker: MockerFixture) -> ProcMock:
    proc_mock = ProcMock()
    # add a default for docker compose version
    proc_mock.set_output(["docker", "compose", "version", "--format", "json"], [json.dumps({"version": "v2.5.0"})])
    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen
    return proc_mock


@pytest.fixture
def app_dir_mock(mocker: MockerFixture, tmp_path: Path) -> AppDirs:
    return tmp_app_dir(mocker, tmp_path)


@pytest.fixture(scope="function")
def mock_questionary_input() -> typing.Iterator[PipeInput]:
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input


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
