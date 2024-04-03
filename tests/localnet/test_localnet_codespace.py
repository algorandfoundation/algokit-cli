import platform

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def test_install_gh_already_installed(mocker: MockerFixture, proc_mock: ProcMock) -> None:
    proc_mock.set_output(["gh", "--version"], ["some version"])
    mocker.patch("algokit.cli.codespace.login_to_gh", return_value=False)
    result = invoke("localnet codespace")
    assert result.exit_code == 0


@pytest.mark.mock_platform_system("Windows")
def test_install_gh_windows(mocker: MockerFixture, proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on(
        ["gh", "--version"],
    )
    proc_mock.set_output(["winget", "install", "--id", "GitHub.cli", "--silent"], [])
    mocker.patch("algokit.cli.codespace.login_to_gh", return_value=False)
    result = invoke("localnet codespace")
    assert result.exit_code == 0

    verify(result.output)


@pytest.mark.skipif(platform.system().lower() == "windows", reason="Test only runs on Unix systems")
def test_install_gh_unix(
    mocker: MockerFixture, proc_mock: ProcMock, httpx_mock: HTTPXMock, tmp_path_factory: pytest.TempPathFactory
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    dummy_script_path = cwd / "webi_dummy_installer.sh"
    dummy_script_path.touch()
    proc_mock.should_fail_on(
        ["gh", "--version"],
    )
    httpx_mock.add_response(url="https://webi.sh/gh", text="")
    mocker.patch("algokit.cli.codespace.login_to_gh", return_value=False)

    # Mock the NamedTemporaryFile to return a mock object with a custom name attribute when used in a context manager
    temp_file_mock = mocker.MagicMock()
    temp_file_mock.__enter__.return_value.name = str(cwd / "webi_dummy_installer.sh")
    mocker.patch("tempfile.NamedTemporaryFile", return_value=temp_file_mock)

    result = invoke("localnet codespace")
    assert result.exit_code == 0
    verify(result.output.replace(str(cwd), "{cwd}"))
