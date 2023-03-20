import json
import os
import sys
import typing
from pathlib import Path

import prompt_toolkit.data_structures
import pytest
from approvaltests import Reporter, reporters, set_default_reporter
from approvaltests.reporters.generic_diff_reporter_config import create_config
from approvaltests.reporters.generic_diff_reporter_factory import GenericDiffReporter
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import PipeInput, create_pipe_input
from prompt_toolkit.output.flush_stdout import flush_stdout
from prompt_toolkit.output.plain_text import PlainTextOutput
from pytest_mock import MockerFixture

from tests.utils.app_dir_mock import AppDirs, tmp_app_dir
from tests.utils.proc_mock import ProcMock


@pytest.fixture
def proc_mock(mocker: MockerFixture) -> ProcMock:
    proc_mock = ProcMock()
    # add a default for docker compose version
    proc_mock.set_output(["docker", "compose", "version", "--format", "json"], [json.dumps({"version": "v2.5.0"})])
    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen
    return proc_mock


@pytest.fixture()
def mock_os_dependency(request: pytest.FixtureRequest, mocker: MockerFixture) -> None:
    # Mock OS.platform
    platform_system: str = getattr(request, "param", "Darwin")
    platform_module = mocker.patch("algokit.core.bootstrap.platform")
    platform_module.system.return_value = platform_system


@pytest.fixture
def app_dir_mock(mocker: MockerFixture, tmp_path: Path) -> AppDirs:
    return tmp_app_dir(mocker, tmp_path)


class CaptureOutput(PlainTextOutput):
    def __init__(self) -> None:
        super().__init__(stdout=sys.stdout)
        self._last_output = ""

    def flush(self) -> None:
        if not self._buffer:
            return

        buffer = "".join(self._buffer)
        self._buffer = []
        lines = [ln.rstrip() for ln in buffer.splitlines() if ln.strip()]
        data = "\n".join(lines) + "\n"
        if data.strip() != self._last_output.strip():
            flush_stdout(sys.stdout, data)
        self._last_output = data

    def scroll_buffer_to_prompt(self) -> None:
        self._last_output = ""

    def get_size(self) -> prompt_toolkit.data_structures.Size:
        return prompt_toolkit.data_structures.Size(rows=10_000, columns=10_000)


@pytest.fixture(scope="function")
def mock_questionary_input() -> typing.Iterator[PipeInput]:
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=CaptureOutput()):
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
