from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def _normalize_path(path: Path) -> str:
    return str(path.absolute()).replace("\\", r"\\")


@pytest.fixture()
def hello_world_contract_path() -> Path:
    return Path(__file__).parent / "hello_world_contract.py"


def test_compile_py_help() -> None:
    result = invoke("compile py -h")

    assert result.exit_code == 0
    verify(result.output)


def test_puyapy_is_not_installed_anywhere(hello_world_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()
    proc_mock.should_bad_exit_on(["poetry", "run", "puyapy", "-h"], exit_code=1, output=["Puyapy not found"])
    proc_mock.should_bad_exit_on(["puyapy", "-h"], exit_code=1, output=["Puyapy not found"])

    proc_mock.set_output(["pipx", "--version"], ["1.0.0"])

    proc_mock.set_output(["pipx", "install", "puya"], ["Puyapy is installed"])
    proc_mock.set_output(["puyapy", str(hello_world_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile py {_normalize_path(hello_world_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_specificed_puyapy_version_is_not_installed(hello_world_contract_path: Path, mocker: MockerFixture) -> None:
    current_version = "1.0.0"
    target_version = "1.1.0"

    proc_mock = ProcMock()
    proc_mock.set_output(["poetry", "run", "puyapy", "--version"], output=[current_version])
    proc_mock.should_bad_exit_on(["puyapy", "--version"], exit_code=1, output=["Puyapy not found"])

    proc_mock.set_output(["pipx", "--version"], ["1.0.0"])
    proc_mock.set_output(["pipx", "run", f"puya=={target_version}", str(hello_world_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile py {_normalize_path(hello_world_contract_path)} --version {target_version}")

    assert result.exit_code == 0
    verify(result.output)


def test_puyapy_is_installed_in_project(hello_world_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()
    proc_mock.set_output(["poetry", "run", "puyapy", "-h"], output=["Puyapy help"])
    proc_mock.set_output(["poetry", "run", "puyapy", str(hello_world_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile py {_normalize_path(hello_world_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_puyapy_is_installed_globally(hello_world_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()
    proc_mock.should_bad_exit_on(["poetry", "run", "puyapy", "-h"], exit_code=1, output=["Puyapy not found"])

    proc_mock.set_output(["puyapy", "-h"], output=["Puyapy help"])
    proc_mock.set_output(["puyapy", str(hello_world_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile py {_normalize_path(hello_world_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)
