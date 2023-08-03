from collections.abc import Callable
from pathlib import Path

import pytest
from _pytest.tmpdir import TempPathFactory
from algokit.core.conf import ALGOKIT_CONFIG
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke
from tests.utils.which_mock import WhichMock

DirWithAppSpecFactory = Callable[[Path], Path]


@pytest.fixture()
def cwd_with_custom_folder(tmp_path_factory: TempPathFactory) -> tuple[Path, str]:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "smart_contract").mkdir()
    # Required for windows compatibility
    return cwd, str((cwd / "smart_contract").absolute()).replace("\\", r"\\")


@pytest.fixture()
def which_mock(mocker: MockerFixture) -> WhichMock:
    which_mock = WhichMock()
    which_mock.add("git")
    mocker.patch("algokit.cli.generate.shutil.which").side_effect = which_mock.which
    return which_mock


def test_generate_custom_generate_commands_no_toml(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke("generate", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)


def test_generate_custom_generate_commands_invalid_generic_generator(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    (cwd / ALGOKIT_CONFIG).write_text(
        """
[generate]
description = "invalid"
path = "invalid"
    """.strip(),
        encoding="utf-8",
    )

    result = invoke("generate", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)


def test_generate_custom_generate_commands_valid_generator(
    cwd_with_custom_folder: tuple[Path, str],
) -> None:
    cwd, smart_contract_path = cwd_with_custom_folder
    (cwd / ALGOKIT_CONFIG).write_text(
        f"""
[generate.smart_contract]
description = "Generates a new smart contract"
path = "{smart_contract_path}"
    """.strip(),
        encoding="utf-8",
    )

    result = invoke("generate", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)


def test_generate_custom_generate_command_missing_git_valid_generator(
    cwd_with_custom_folder: tuple[Path, str], which_mock: WhichMock
) -> None:
    which_mock.remove("git")

    cwd, smart_contract_path = cwd_with_custom_folder
    (cwd / ALGOKIT_CONFIG).write_text(
        f"""
[generate.smart_contract]
description = "Generates a new smart contract"
path = "{smart_contract_path}"
    """.strip(),
        encoding="utf-8",
    )

    result = invoke("generate smart-contract", cwd=cwd)

    assert result.exit_code == 1
    verify(result.output)


def test_generate_custom_generate_commands_valid_generator_run(
    cwd_with_custom_folder: tuple[Path, str], mocker: MockerFixture
) -> None:
    cwd, smart_contract_path = cwd_with_custom_folder
    (cwd / ALGOKIT_CONFIG).write_text(
        f"""
[generate.smart_contract]
description = "Generates a new smart contract"
path = "{smart_contract_path}"
    """.strip(),
        encoding="utf-8",
    )
    mock_copier_worker_cls = mocker.patch("copier.main.Worker")
    mock_copier_worker_cls.return_value.__enter__.return_value.src_path = str(cwd / "smart_contract")

    result = invoke("generate smart-contract", cwd=cwd)

    assert result.exit_code == 0
    assert mock_copier_worker_cls.call_args.kwargs["src_path"] == str(cwd / "smart_contract")
    verify(result.output)


def test_generate_custom_generate_commands_valid_generator_no_description(
    cwd_with_custom_folder: tuple[Path, str]
) -> None:
    cwd, smart_contract_path = cwd_with_custom_folder
    (cwd / ALGOKIT_CONFIG).write_text(
        f"""
[generate.smart_contract]
path = "{smart_contract_path}"
    """.strip(),
        encoding="utf-8",
    )

    result = invoke("generate", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)


def test_generate_custom_generate_commands_valid_generator_invalid_path(
    tmp_path_factory: TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ALGOKIT_CONFIG).write_text(
        """
[generate.smart_contract]
description = "Generates a new smart contract"
path = "invalidpath"
    """.strip(),
        encoding="utf-8",
    )

    result = invoke("generate", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)
