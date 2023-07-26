from collections.abc import Callable
from pathlib import Path

from _pytest.tmpdir import TempPathFactory
from algokit.core.conf import ALGOKIT_CONFIG
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke

DirWithAppSpecFactory = Callable[[Path], Path]


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
    tmp_path_factory: TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "smart_contract").mkdir()
    (cwd / ALGOKIT_CONFIG).write_text(
        f"""
[generate.smart_contract]
description = "Generates a new smart contract"
path = "{cwd/"smart_contract"}"
    """.strip(),
        encoding="utf-8",
    )

    result = invoke("generate", cwd=cwd)

    assert result.exit_code == 0
    verify(result.output)


def test_generate_custom_generate_commands_valid_generator_run(
    tmp_path_factory: TempPathFactory, mocker: MockerFixture
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "smart_contract").mkdir()
    (cwd / ALGOKIT_CONFIG).write_text(
        f"""
[generate.smart_contract]
description = "Generates a new smart contract"
path = "{cwd/"smart_contract"}"
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
    tmp_path_factory: TempPathFactory,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "smart_contract").mkdir()
    (cwd / ALGOKIT_CONFIG).write_text(
        f"""
[generate.smart_contract]
path = "{cwd/"smart_contract"}"
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
