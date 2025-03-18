import logging
import os
import subprocess
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


def _command_name_scrubber(output: str) -> str:
    """Scrubber to normalize command names between Windows and non-Windows platforms."""
    return (
        output.replace("npm.cmd", "npm")
        .replace("npx.cmd", "npx")
        .replace("DEBUG: npm.cmd:", "DEBUG: npm:")
        .replace("DEBUG: npx.cmd:", "DEBUG: npx:")
        .replace("Running 'npm.cmd", "Running 'npm")
        .replace("Running 'npx.cmd", "Running 'npx")
    )


@pytest.fixture()
def dummy_contract_path() -> Path:
    return Path(__file__).parent / "dummy_contract.py"


@pytest.fixture(autouse=True)
def cwd(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("cwd", numbered=True)


@pytest.fixture()
def output_path(cwd: Path) -> Path:
    return cwd / "output"


@pytest.fixture()
def typescript_test_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    # Create a test directory
    test_dir = tmp_path_factory.mktemp("ts_test", numbered=True)

    # Create package.json with required dependencies
    package_json_content = """{
        "name": "algokit-test",
        "version": "1.0.0",
        "dependencies": {
            "@algorandfoundation/puya-ts": "^1.0.0-beta.48",
            "@algorandfoundation/algorand-typescript": "^1.0.0-beta.25"
        }
    }"""

    package_json_path = test_dir / "package.json"
    package_json_path.write_text(package_json_content)

    # Execute npm install in the directory
    subprocess.run([_get_npm_command(), "install"], cwd=test_dir, check=True, capture_output=True, text=True)

    return test_dir


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
    verify(result.output, scrubber=_command_name_scrubber)


def test_puyats_is_not_installed_anywhere(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    proc_mock = ProcMock()

    # Mock npm ls for project and global scopes with no PuyaTs found
    proc_mock.set_output([_get_npm_command(), "ls"], ["STDOUT", "STDERR"])
    proc_mock.set_output([_get_npm_command(), "--global", "ls"], ["STDOUT", "STDERR"])

    # Mock successful npx execution
    proc_mock.set_output(
        [_get_npx_command(), "-y", PUYATS_NPM_PACKAGE, str(dummy_contract_path)],
        ["Compilation successful"],
    )

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile typescript {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output, scrubber=_command_name_scrubber)


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
        [
            _get_npx_command(),
            "-y",
            f"{PUYATS_NPM_PACKAGE}@{target_version}",
            str(dummy_contract_path),
        ],
        ["Compilation successful"],
    )

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile --version {target_version} typescript {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output, scrubber=_command_name_scrubber)


def test_puyats_is_installed_in_project(dummy_contract_path: Path, mocker: MockerFixture) -> None:
    version = "1.0.0"
    proc_mock = ProcMock()

    # Mock npm ls for project with PuyaTs installed
    proc_mock.set_output([_get_npm_command(), "ls"], [f"└── {PUYATS_NPM_PACKAGE}@{version}"])

    # Ensure version check passes for project version
    proc_mock.set_output([_get_npx_command(), PUYATS_NPM_PACKAGE, "--version"], [f"puya-ts {version}"])

    # Mock successful compile with project installation
    proc_mock.set_output(
        [_get_npx_command(), PUYATS_NPM_PACKAGE, str(dummy_contract_path)],
        ["Compilation successful"],
    )

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile typescript {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output, scrubber=_command_name_scrubber)


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
    proc_mock.set_output(
        [_get_npx_command(), PUYATS_NPM_PACKAGE, str(dummy_contract_path)],
        ["Compilation successful"],
    )

    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen

    result = invoke(f"compile typescript {_normalize_path(dummy_contract_path)}")

    assert result.exit_code == 0
    verify(result.output, scrubber=_command_name_scrubber)


# Test with locally installed PuyaTs compiler
def test_valid_contract(typescript_test_dir: Path) -> None:
    # Create a contract file
    contract_path = typescript_test_dir / "contract.algo.ts"
    contract_path.write_text(VALID_ALGORAND_TYPESCRIPT_CONTRACT_FILE_CONTENT)

    # Run algokit compile with proper Node.js stack size setting
    result = invoke(
        "compile typescript contract.algo.ts --out-dir output",
        cwd=typescript_test_dir,
    )

    # Check the results
    assert result.exit_code == 0
    # Verify output files exist
    assert (typescript_test_dir / "output" / "HelloWorld.approval.puya.map").exists()
    assert (typescript_test_dir / "output" / "HelloWorld.approval.teal").exists()
    assert (typescript_test_dir / "output" / "HelloWorld.arc32.json").exists()
    assert (typescript_test_dir / "output" / "HelloWorld.arc56.json").exists()
    assert (typescript_test_dir / "output" / "HelloWorld.clear.puya.map").exists()
    assert (typescript_test_dir / "output" / "HelloWorld.clear.teal").exists()


# Test with locally installed PuyaTs compiler
def test_invalid_contract(typescript_test_dir: Path) -> None:
    # Create a contract file
    contract_path = typescript_test_dir / "contract.algo.ts"
    contract_path.write_text(INVALID_ALGORAND_TYPESCRIPT_CONTRACT_FILE_CONTENT)

    # Run algokit compile with proper Node.js stack size setting
    result = invoke(
        "compile typescript contract.algo.ts --out-dir output",
        cwd=typescript_test_dir,
    )

    # Check the results
    assert result.exit_code == 1
    # Verify output files exist
    assert "Compilation halted due to parse errors" in result.output
