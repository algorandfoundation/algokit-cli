import logging

import pytest
from approvaltests.namer import NamerFactory
from pytest_mock import MockerFixture

from tests import get_combined_verify_output
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.mark.parametrize("command", ["", "localnet", "testnet", "mainnet"])
def test_explore(command: str, mocker: MockerFixture) -> None:
    launch_mock = mocker.patch("click.launch")
    result = invoke(f"explore {command}")

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(result.output, "launch args", launch_mock.call_args),
        options=NamerFactory.with_parameters(command or "localnet"),
    )


def test_explore_wsl_exception(mocker: MockerFixture, caplog: pytest.LogCaptureFixture) -> None:
    command = "localnet"
    mocker.patch("algokit.cli.explore.is_wsl", return_value=True)
    mocker.patch("webbrowser.open", side_effect=Exception("Test Exception"))

    with caplog.at_level(logging.WARNING):
        result = invoke(f"explore {command}")

    assert result.exit_code == 0
    assert any("Unable to open browser from WSL" in message for message in caplog.messages)


def test_explore_webbrowser_exception(mocker: MockerFixture, caplog: pytest.LogCaptureFixture) -> None:
    command = "localnet"
    mocker.patch("algokit.cli.explore.is_wsl", return_value=False)
    mocker.patch("click.launch", side_effect=Exception("Click Exception"))
    mocker.patch("webbrowser.open", side_effect=Exception("Webbrowser Exception"))

    with caplog.at_level(logging.WARNING):
        result = invoke(f"explore {command}")

    assert result.exit_code == 0
    assert any("Failed to open browser. Please open this URL manually:" in message for message in caplog.messages)
