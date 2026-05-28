from pathlib import Path
from typing import cast

import pytest
from pytest_mock import MockerFixture

from algokit.cli.init.command import _maybe_setup_vibecode


@pytest.mark.parametrize("run_bootstrap", [True, False, None])
def test_maybe_setup_vibecode_skips_when_using_defaults(mocker: MockerFixture, run_bootstrap: object) -> None:
    prompt_mock = mocker.patch("algokit.cli.init.command.questionary_extensions.prompt_confirm")
    vibe_setup_mock = mocker.patch("algokit.cli.vibe.run_vibe_setup")

    _maybe_setup_vibecode(
        project_path=Path("/tmp/project"),
        use_defaults=True,
        run_bootstrap=cast("bool | None", run_bootstrap),
    )

    prompt_mock.assert_not_called()
    vibe_setup_mock.assert_not_called()


@pytest.mark.parametrize("run_bootstrap", [True, False])
def test_maybe_setup_vibecode_skips_when_bootstrap_flag_is_explicit(
    mocker: MockerFixture, run_bootstrap: object
) -> None:
    prompt_mock = mocker.patch("algokit.cli.init.command.questionary_extensions.prompt_confirm")
    vibe_setup_mock = mocker.patch("algokit.cli.vibe.run_vibe_setup")

    _maybe_setup_vibecode(
        project_path=Path("/tmp/project"),
        use_defaults=False,
        run_bootstrap=cast("bool", run_bootstrap),
    )

    prompt_mock.assert_not_called()
    vibe_setup_mock.assert_not_called()


def test_maybe_setup_vibecode_prompt_no(mocker: MockerFixture) -> None:
    prompt_mock = mocker.patch("algokit.cli.init.command.questionary_extensions.prompt_confirm", return_value=False)
    vibe_setup_mock = mocker.patch("algokit.cli.vibe.run_vibe_setup")

    _maybe_setup_vibecode(project_path=Path("/tmp/project"), use_defaults=False, run_bootstrap=None)

    prompt_mock.assert_called_once()
    vibe_setup_mock.assert_not_called()


def test_maybe_setup_vibecode_prompt_yes_runs_setup_in_project_dir(mocker: MockerFixture) -> None:
    prompt_mock = mocker.patch("algokit.cli.init.command.questionary_extensions.prompt_confirm", return_value=True)
    vibe_setup_mock = mocker.patch("algokit.cli.vibe.run_vibe_setup")
    project_path = Path("/tmp/project")

    _maybe_setup_vibecode(project_path=project_path, use_defaults=False, run_bootstrap=None)

    prompt_mock.assert_called_once()
    vibe_setup_mock.assert_called_once_with(cwd=project_path)


def test_maybe_setup_vibecode_setup_error_does_not_raise(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.init.command.questionary_extensions.prompt_confirm", return_value=True)
    mocker.patch("algokit.cli.vibe.run_vibe_setup", side_effect=RuntimeError("boom"))

    _maybe_setup_vibecode(project_path=Path("/tmp/project"), use_defaults=False, run_bootstrap=None)
