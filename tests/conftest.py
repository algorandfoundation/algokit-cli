import functools
import json
import logging
import os
import subprocess
import typing
from collections.abc import Callable, Sequence  # noqa: RUF100, TCH003
from pathlib import Path

import pytest
import questionary
from algokit.core import questionary_extensions
from approvaltests import Reporter, reporters, set_default_reporter
from approvaltests.reporters.generic_diff_reporter_config import create_config
from approvaltests.reporters.generic_diff_reporter_factory import GenericDiffReporter
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import PipeInput, create_pipe_input
from prompt_toolkit.output import DummyOutput
from pytest_mock import MockerFixture

from tests.utils.app_dir_mock import AppDirs, tmp_app_dir
from tests.utils.proc_mock import ProcMock


@pytest.fixture()
def proc_mock(mocker: MockerFixture) -> ProcMock:
    proc_mock = ProcMock()
    # add a default for docker compose version
    proc_mock.set_output(["docker", "compose", "version", "--format", "json"], [json.dumps({"version": "v2.5.0"})])
    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen
    return proc_mock


def _do_platform_mock(platform_system: str, monkeypatch: pytest.MonkeyPatch) -> None:
    import platform

    monkeypatch.setattr(platform, "system", lambda: platform_system)
    monkeypatch.setattr(platform, "platform", lambda: f"{platform_system}-other-system-info")


@pytest.fixture(
    params=[
        pytest.param("Windows", id="windows"),
        pytest.param("Linux", id="linux"),
        pytest.param("Darwin", id="macOS"),
    ]
)
def mock_platform_system(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> str:
    platform_system: str = request.param
    _do_platform_mock(platform_system=platform_system, monkeypatch=monkeypatch)
    return platform_system


@pytest.fixture(autouse=True)
def _mock_platform_system_marker(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = request.node.get_closest_marker("mock_platform_system")
    if marker is not None:
        _do_platform_mock(platform_system=marker.args[0], monkeypatch=monkeypatch)


@pytest.fixture()
def app_dir_mock(mocker: MockerFixture, tmp_path: Path) -> AppDirs:
    return tmp_app_dir(mocker, tmp_path)


@pytest.fixture()
def mock_questionary_input() -> typing.Iterator[PipeInput]:
    with create_pipe_input() as pipe_input, create_app_session(input=pipe_input, output=DummyOutput()):
        yield pipe_input


@pytest.fixture(autouse=True)
def _supress_copier_dependencies_debug_output() -> None:
    logging.getLogger("plumbum.local").setLevel("INFO")
    logging.getLogger("asyncio").setLevel("INFO")


Params = typing.ParamSpec("Params")
Result = typing.TypeVar("Result")


def intercept(
    f: typing.Callable[Params, Result], interceptor: typing.Callable[Params, None]
) -> typing.Callable[Params, Result]:
    @functools.wraps(f)
    def wrapped(*args: Params.args, **kwargs: Params.kwargs) -> Result:
        interceptor(*args, **kwargs)
        return f(*args, **kwargs)

    return wrapped


@pytest.fixture(autouse=True)
def _patch_questionary_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    ValidatorsType = Sequence[type[questionary.Validator] | questionary.Validator | Callable[[str], bool]]  # noqa: N806

    def log_prompt_text(
        message: str,
        *,
        validators: ValidatorsType | None = None,  # noqa: ARG001
        validate_while_typing: bool = False,  # noqa: ARG001
    ) -> None:
        print(f"? {message}")  # noqa: T201

    def log_prompt_select(
        message: str,
        *choices: str | questionary.Choice,
    ) -> None:
        print(f"? {message}")  # noqa: T201
        for choice in choices:
            print(  # noqa: T201
                (choice.value if choice.title is None else "".join([token[1] for token in choice.title]))
                if isinstance(choice, questionary.Choice)
                else choice
            )

    def log_prompt_confirm(message: str, *, default: bool) -> None:
        if default:
            default_text = "(Y/n)"
        else:
            default_text = "(y/N)"
        print(f"? {message} {default_text}")  # noqa: T201

    monkeypatch.setattr(
        questionary_extensions,
        "prompt_text",
        intercept(questionary_extensions.prompt_text, log_prompt_text),
    )
    monkeypatch.setattr(
        questionary_extensions,
        "prompt_select",
        intercept(questionary_extensions.prompt_select, log_prompt_select),
    )
    monkeypatch.setattr(
        questionary_extensions,
        "prompt_confirm",
        intercept(questionary_extensions.prompt_confirm, log_prompt_confirm),
    )


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


@pytest.fixture()
def mock_keyring(mocker: MockerFixture) -> typing.Generator[dict[str, str | None], None, None]:
    credentials: dict[str, str | None] = {}

    def _get_password(service_name: str, username: str) -> str | None:  # noqa: ARG001
        return credentials[username]

    def _set_password(service_name: str, username: str, password: str) -> None:  # noqa: ARG001
        credentials[username] = password

    def _delete_password(service_name: str, username: str) -> None:  # noqa: ARG001
        del credentials[username]

    mocker.patch("keyring.get_password", side_effect=_get_password)
    mocker.patch("keyring.set_password", side_effect=_set_password)
    mocker.patch("keyring.delete_password", side_effect=_delete_password)

    yield credentials

    # Teardown step: reset the credentials
    for key in credentials:
        credentials[key] = None


@pytest.fixture()
def dummy_algokit_template_with_python_task(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """
    Used in init approval tests and binary portability tests
    """

    cwd = tmp_path_factory.mktemp("cwd")
    dummy_template_path = cwd / "dummy_template"
    dummy_template_path.mkdir()
    (dummy_template_path / "copier.yaml").write_text(
        """
        _tasks:
            - "echo '==== 1/1 - Emulate fullstack template python task ===='"
            - '{{ python_path }} -c ''print("hello world")'''

        python_path:
            type: str
            help: Path to the sys.executable.
        """
    )
    subprocess.run(["git", "init"], cwd=dummy_template_path, check=False)
    subprocess.run(["git", "add", "."], cwd=dummy_template_path, check=False)
    subprocess.run(["git", "commit", "-m", "chore: setup dummy test template"], cwd=dummy_template_path, check=False)
    return {"template_path": dummy_template_path, "cwd": cwd}
