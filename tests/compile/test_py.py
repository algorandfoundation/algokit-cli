import os
from pathlib import Path

import pytest
from approvaltests.namer import NamerFactory
from pytest_mock import MockerFixture

from tests.compile.conftest import INVALID_PUYA_CONTRACT_FILE_CONTENT, VALID_PUYA_CONTRACT_FILE_CONTENT
from tests.utils.approvals import normalize_path, verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock


def _normalize_path(path: Path) -> str:
    return str(path.absolute()).replace("\\", r"\\")


@pytest.fixture()
def dummy_contract_path() -> Path:
    return Path(__file__).parent / "dummy_contract.py"


@pytest.fixture(autouse=True)
def cwd(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("cwd", numbered=True)


@pytest.fixture()
def output_path(cwd: Path) -> Path:
    return cwd / "output"


def test_compile_py_help(mocker: MockerFixture) -> None:
    proc_mock = ProcMock()
    proc_mock.set_output(["poetry", "run", "puyapy", "-h"], output=["Puyapy help"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen
    result = invoke("compile py -h")

    assert result.exit_code == 0
    verify(result.output)


def test_puyapy_is_not_installed_anywhere(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()
    proc_mock.should_bad_exit_on(["poetry", "run", "puyapy", "-h"], exit_code=1, output=["Puyapy not found"])
    proc_mock.should_bad_exit_on(["puyapy", "-h"], exit_code=1, output=["Puyapy not found"])

    proc_mock.set_output(["pipx", "--version"], ["1.0.0"])

    proc_mock.set_output(["pipx", "install", "puya"], ["Puyapy is installed"])
    proc_mock.set_output(["puyapy", str(dummy_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile py {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_specificed_puyapy_version_is_not_installed(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    current_version = "1.0.0"
    target_version = "1.1.0"

    proc_mock = ProcMock()
    proc_mock.set_output(["poetry", "run", "puyapy", "--version"], output=[current_version])
    proc_mock.should_bad_exit_on(["puyapy", "--version"], exit_code=1, output=["Puyapy not found"])

    proc_mock.set_output(["pipx", "--version"], ["1.0.0"])
    proc_mock.set_output(["pipx", "run", f"puya=={target_version}", str(dummy_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile --version {target_version} py {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_puyapy_is_installed_in_project(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()
    proc_mock.set_output(["poetry", "run", "puyapy", "-h"], output=["Puyapy help"])
    proc_mock.set_output(["poetry", "run", "puyapy", str(dummy_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile py {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_puyapy_is_installed_globally(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()
    proc_mock.should_bad_exit_on(["poetry", "run", "puyapy", "-h"], exit_code=1, output=["Puyapy not found"])

    proc_mock.set_output(["puyapy", "-h"], output=["Puyapy help"])
    proc_mock.set_output(["puyapy", str(dummy_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile py {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_valid_contract(cwd: Path, output_path: Path) -> None:
    contract_path = cwd / "contract.py"
    contract_path.write_text(VALID_PUYA_CONTRACT_FILE_CONTENT)
    result = invoke(f"compile py {_normalize_path(contract_path)} --out-dir {_normalize_path(output_path)}")

    assert result.exit_code == 0

    for d, __, files in os.walk(output_path):
        for file in files:
            content = (d / Path(file)).read_text()
            normalize_content = normalize_path(content, str(cwd), "{temp_output_directory}")
            verify(normalize_content, options=NamerFactory.with_parameters(file))


def test_invalid_contract(cwd: Path, output_path: Path) -> None:
    contract_path = cwd / "contract.py"
    contract_path.write_text(INVALID_PUYA_CONTRACT_FILE_CONTENT)
    result = invoke(f"compile py {_normalize_path(contract_path)} --out-dir {_normalize_path(output_path)}")

    assert result.exit_code == 1

    normalize_output = normalize_path(result.output, str(cwd), "{temp_output_directory}")
    verify(normalize_output)
