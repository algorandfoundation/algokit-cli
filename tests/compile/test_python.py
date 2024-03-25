import logging
import os
import sys
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from tests.compile.conftest import (
    INVALID_ALGORAND_PYTHON_CONTRACT_FILE_CONTENT,
    VALID_ALGORAND_PYTHON_CONTRACT_FILE_CONTENT,
)
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock

logger = logging.getLogger(__name__)


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
    result = invoke("compile python -h")

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

    result = invoke(f"compile python {_normalize_path(dummy_contract_path)}")

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

    result = invoke(f"compile python {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_puyapy_is_installed_globally(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()
    proc_mock.should_bad_exit_on(["poetry", "run", "puyapy", "-h"], exit_code=1, output=["Puyapy not found"])

    proc_mock.set_output(["puyapy", "-h"], output=["Puyapy help"])
    proc_mock.set_output(["puyapy", str(dummy_contract_path)], ["Done"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile python {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


@pytest.mark.skipif(sys.version_info < (3, 12), reason="PuyaPy requires python3.12 or higher")
def test_valid_contract(cwd: Path, output_path: Path) -> None:
    # Set NO_COLOR to 1 to avoid requirements for colorama on Windows
    logger.debug(f"sys.version_info {sys.version_info}")
    os.environ["NO_COLOR"] = "1"

    contract_path = cwd / "contract.py"
    contract_path.write_text(VALID_ALGORAND_PYTHON_CONTRACT_FILE_CONTENT)

    result = invoke(f"compile python {_normalize_path(contract_path)} --out-dir {_normalize_path(output_path)}")

    # Only check for the exit code, don't check the results from PuyaPy
    assert result.exit_code == 0


@pytest.mark.skipif(sys.version_info < (3, 12), reason="PuyaPy requires python3.12 or higher")
def test_invalid_contract(cwd: Path, output_path: Path) -> None:
    # Set NO_COLOR to 1 to avoid requirements for colorama on Windows
    os.environ["NO_COLOR"] = "1"

    contract_path = cwd / "contract.py"
    contract_path.write_text(INVALID_ALGORAND_PYTHON_CONTRACT_FILE_CONTENT)
    result = invoke(f"compile python {_normalize_path(contract_path)} --out-dir {_normalize_path(output_path)}")

    # Only check for the exit code and the error message from AlgoKit CLI
    assert result.exit_code == 1
    result.output.endswith(
        "An error occurred during compile. Ensure supplied files are valid PuyaPy code before retrying."
    )
