import platform
from subprocess import CompletedProcess

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def test_install_gh_already_installed(mocker: MockerFixture, proc_mock: ProcMock) -> None:
    proc_mock.set_output(["gh", "--version"], ["some version"])
    mocker.patch("algokit.cli.codespace.authenticate_with_github", return_value=False)
    result = invoke("localnet codespace")
    assert result.exit_code == 0


def test_install_gh_not_installed_failed_install(mocker: MockerFixture, proc_mock: ProcMock) -> None:
    proc_mock.should_fail_on(["gh", "--version"])
    mocker.patch("algokit.cli.codespace.authenticate_with_github", return_value=False)
    mocker.patch("algokit.core.codespace.install_github_cli_via_webi", side_effect=RuntimeError("Failed to install gh"))
    mocker.patch("algokit.core.codespace.is_windows", side_effect=RuntimeError("Failed to install gh"))
    result = invoke("localnet codespace")
    assert result.exit_code == 1
    verify(result.output)


@pytest.mark.mock_platform_system("Windows")
def test_install_gh_windows(
    mocker: MockerFixture, proc_mock: ProcMock, tmp_path_factory: pytest.TempPathFactory
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    dummy_script_path = cwd / "webi_dummy_installer.ps1"
    dummy_script_path.touch()

    proc_mock.should_fail_on(
        ["gh", "--version"],
    )
    proc_mock.set_output(
        ["powershell", "-command", "(Get-Variable PSVersionTable -ValueOnly).PSVersion"], ["PowerShell 7.2.1"]
    )
    proc_mock.set_output(
        [
            "powershell",
            "-File",
            str(dummy_script_path),
        ],
        ["installed gh!"],
    )
    mocker.patch("algokit.cli.codespace.authenticate_with_github", return_value=False)
    temp_file_mock = mocker.MagicMock()
    temp_file_mock.__enter__.return_value.name = str(dummy_script_path)
    mocker.patch("tempfile.NamedTemporaryFile", return_value=temp_file_mock)

    result = invoke("localnet codespace")
    assert result.exit_code == 0

    verify(result.output.replace(str(dummy_script_path), "{dummy_script_path}"))


@pytest.mark.skipif(platform.system().lower() == "windows", reason="Test only runs on Unix systems")
def test_install_gh_unix(
    mocker: MockerFixture, proc_mock: ProcMock, httpx_mock: HTTPXMock, tmp_path_factory: pytest.TempPathFactory
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    dummy_script_path = cwd / "webi_dummy_installer.sh"
    dummy_script_path.touch()
    proc_mock.set_output(["bash", "--version"], ["GNU bash, version 3.2.57(1)-release"])
    proc_mock.should_fail_on(
        ["gh", "--version"],
    )
    proc_mock.set_output(["bash", str(dummy_script_path)], ["installed gh!"])
    httpx_mock.add_response(url="https://webi.sh/gh", text="")
    mocker.patch("algokit.cli.codespace.authenticate_with_github", return_value=False)

    temp_file_mock = mocker.MagicMock()
    temp_file_mock.__enter__.return_value.name = str(cwd / "webi_dummy_installer.sh")
    mocker.patch("tempfile.NamedTemporaryFile", return_value=temp_file_mock)

    result = invoke("localnet codespace")
    assert result.exit_code == 0
    verify(result.output.replace(str(cwd), "{cwd}"))


def test_invalid_scope_auth(
    mocker: MockerFixture, proc_mock: ProcMock, tmp_path_factory: pytest.TempPathFactory
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    dummy_script_path = cwd / "webi_dummy_installer.sh"
    dummy_script_path.touch()
    proc_mock.set_output(
        ["gh", "auth", "status"],
        [
            """
  ✓ Logged in to github.com account aorumbayev (keyring)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_************************************
  - Token scopes: 'read:org', 'repo', 'workflow'
"""
        ],
    )
    mocker.patch("algokit.core.proc.subprocess_run").return_value = CompletedProcess(
        args=["docker", "exec"], returncode=0, stdout="logged in!"
    )
    proc_mock.set_output(
        [
            "gh",
            "codespace",
            "create",
            "--repo",
            "algorandfoundation/algokit-base-template",
            "--display-name",
            "sandbox",
            "--machine",
            "basicLinux32gb",
        ],
        [],
    )
    proc_mock.set_output(
        ["gh", "codespace", "list", "--json", "displayName", "--json", "state", "--json", "name"],
        [
            """
            [{"displayName":"sandbox","state":"Available","name":"sandbox"}]
            """
        ],
    )
    proc_mock.set_output(
        ["gh", "codespace", "delete", "--codespace", "sandbox", "--force"], ["Deleted unused codespace"]
    )
    mocker.patch("algokit.cli.codespace.forward_ports_for_codespace", return_value=None)
    mocker.patch("algokit.core.codespace.run_with_animation")

    result = invoke("localnet codespace -n sandbox --force")
    assert result.exit_code == 0
    verify(result.output)
