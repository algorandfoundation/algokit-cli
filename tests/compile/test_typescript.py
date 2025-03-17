import logging
import os
from pathlib import Path

import pytest
from algokit.core.compilers.typescript import PUYATS_NPM_PACKAGE
from pytest_mock import MockerFixture

from tests.compile.conftest import (
    INVALID_ALGORAND_TYPESCRIPT_CONTRACT_FILE_CONTENT,
    VALID_ALGORAND_TYPESCRIPT_CONTRACT_FILE_CONTENT,
)
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.proc_mock import ProcMock

logger = logging.getLogger(__name__)


def _normalize_path(path: Path) -> str:
    return str(path.absolute()).replace("\\", r"\\")


def _get_npm_command() -> str:
    return "npm" if os.name != "nt" else "npm.cmd"


def _get_npx_command() -> str:
    return "npx" if os.name != "nt" else "npx.cmd"


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

    # Mock npm ls for project and global scopes with no PuyaTs found
    proc_mock.set_output([_get_npm_command(), "ls"], ["STDOUT", "STDERR"])
    proc_mock.set_output([_get_npm_command(), "--global", "ls"], ["STDOUT", "STDERR"])

    # Mock the help command
    proc_mock.set_output([_get_npx_command(), "-y", PUYATS_NPM_PACKAGE, "-h"], output=["PuyaTs help"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen
    result = invoke("compile typescript -h")

    assert result.exit_code == 0
    verify(result.output)


def test_puyats_is_not_installed_anywhere(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()

    # Mock npm ls for project and global scopes with no PuyaTs found
    proc_mock.set_output([_get_npm_command(), "ls"], ["STDOUT", "STDERR"])
    proc_mock.set_output([_get_npm_command(), "--global", "ls"], ["STDOUT", "STDERR"])

    # Mock successful npx execution
    proc_mock.set_output(
        [_get_npx_command(), "-y", PUYATS_NPM_PACKAGE, str(dummy_contract_path)], ["Compilation successful"]
    )

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile typescript {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_specificed_puyats_version_is_not_installed(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    current_version = "1.0.0"
    target_version = "1.1.0"

    proc_mock = ProcMock()

    # Mock npm ls for project with a different version installed
    proc_mock.set_output([_get_npm_command(), "ls"], [f"└── {PUYATS_NPM_PACKAGE}@{current_version}"])

    # Mock npm ls for global with a different version installed
    proc_mock.set_output([_get_npm_command(), "--global", "ls"], [f"└── {PUYATS_NPM_PACKAGE}@{current_version}"])

    # Mock successful npx execution with version-specific package
    proc_mock.set_output(
        [_get_npx_command(), "-y", f"{PUYATS_NPM_PACKAGE}@{target_version}", str(dummy_contract_path)],
        ["Compilation successful"],
    )

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile --version {target_version} typescript {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_puyats_is_installed_in_project(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    version = "1.0.0"
    proc_mock = ProcMock()

    # Mock npm ls for project with PuyaTs installed
    proc_mock.set_output([_get_npm_command(), "ls"], [f"└── {PUYATS_NPM_PACKAGE}@{version}"])

    # Ensure version check passes for project version
    proc_mock.set_output([_get_npx_command(), PUYATS_NPM_PACKAGE, "--version"], [f"puya-ts {version}"])

    # Mock successful compile with project installation
    proc_mock.set_output([_get_npx_command(), PUYATS_NPM_PACKAGE, str(dummy_contract_path)], ["Compilation successful"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile typescript {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


def test_puyats_is_installed_globally(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    version = "1.0.0"
    proc_mock = ProcMock()

    # Mock npm ls for project with no installation
    proc_mock.set_output([_get_npm_command(), "ls"], ["STDOUT", "STDERR"])

    # Mock npm ls for global with PuyaTs installed
    proc_mock.set_output([_get_npm_command(), "--global", "ls"], [f"└── {PUYATS_NPM_PACKAGE}@{version}"])

    # Ensure version check passes for global installation
    proc_mock.set_output([_get_npx_command(), PUYATS_NPM_PACKAGE, "--version"], [f"puya-ts {version}"])

    # Mock successful compile with global installation
    proc_mock.set_output([_get_npx_command(), PUYATS_NPM_PACKAGE, str(dummy_contract_path)], ["Compilation successful"])

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile typescript {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output)


# Test with real (not mocked) PuyaTs compiler, similar to the Python tests
def test_valid_contract(cwd: Path, output_path: Path) -> None:
    contract_path = cwd / "contract.algo.ts"
    contract_path.write_text(VALID_ALGORAND_TYPESCRIPT_CONTRACT_FILE_CONTENT)

    result = invoke(
        f"--no-color compile typescript {_normalize_path(contract_path)} --out-dir {_normalize_path(output_path)}"
    )

    # Only check for the exit code, don't check the results from PuyaTs
    assert result.exit_code == 0


# Test with real (not mocked) PuyaTs compiler, similar to the Python tests
def test_invalid_contract(cwd: Path, output_path: Path) -> None:
    # Set NO_COLOR to 1 to avoid requirements for colorama on Windows
    os.environ["NO_COLOR"] = "1"

    contract_path = cwd / "contract.algo.ts"
    contract_path.write_text(INVALID_ALGORAND_TYPESCRIPT_CONTRACT_FILE_CONTENT)
    result = invoke(f"compile typescript {_normalize_path(contract_path)} --out-dir {_normalize_path(output_path)}")

    # Only check for the exit code and the error message from AlgoKit CLI
    assert result.exit_code == 1
    result.output.endswith(
        "An error occurred during compile. Ensure supplied files are valid PuyaPy code before retrying."
    )
