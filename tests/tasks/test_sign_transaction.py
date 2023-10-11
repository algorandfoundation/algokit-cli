import json

import click
import pytest
from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from algosdk import encoding, mnemonic, transaction

from tests.tasks.conftest import DUMMY_ACCOUNT, DUMMY_SUGGESTED_PARAMS
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def _generate_dummy_txn(sender: str, amount: int = 1) -> transaction.PaymentTxn:
    return transaction.PaymentTxn(sender, DUMMY_SUGGESTED_PARAMS, sender, amt=amount)  # type: ignore[no-untyped-call]


def _get_mnemonic_from_private_key(private_key: str) -> str:
    return str(mnemonic.from_private_key(private_key))  # type: ignore[no-untyped-call]


def test_sign_atomic_txn_group_successful(
    tmp_path_factory: pytest.TempPathFactory, mock_keyring: dict[str, str]
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {"alias": alias_name, "address": DUMMY_ACCOUNT.address, "private_key": DUMMY_ACCOUNT.private_key}
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])
    txn_a = _generate_dummy_txn(DUMMY_ACCOUNT.address)
    txn_b = _generate_dummy_txn(DUMMY_ACCOUNT.address)
    gid = transaction.calculate_group_id([txn_a, txn_b])  # type: ignore[no-untyped-call]
    txn_a.group = gid
    txn_b.group = gid
    transaction.write_to_file([txn_a, txn_b], str(cwd / "dummy.txns"))  # type: ignore[no-untyped-call]

    # Act
    result = invoke(f"task sign -a {alias_name} --file dummy.txns", input="y", cwd=cwd)

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_sign_from_stdin_with_alias_successful(mock_keyring: dict[str, str]) -> None:
    # Arrange
    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {"alias": alias_name, "address": DUMMY_ACCOUNT.address, "private_key": DUMMY_ACCOUNT.private_key}
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])
    dummy_txn = _generate_dummy_txn(DUMMY_ACCOUNT.address)

    # Act
    result = invoke(
        f"task sign -a {alias_name} --transaction {encoding.msgpack_encode({'txn': dummy_txn.dictify()})}", input="y"  # type: ignore[no-untyped-call]  # noqa: E501
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_sign_from_stdin_with_address_successful() -> None:
    # Arrange
    dummy_txn = _generate_dummy_txn(DUMMY_ACCOUNT.address)

    # Act
    result = invoke(
        f"task sign -a {DUMMY_ACCOUNT.address} --transaction {encoding.msgpack_encode({'txn': dummy_txn.dictify()})}",  # type: ignore[no-untyped-call]  # noqa: E501
        input=f"{_get_mnemonic_from_private_key(DUMMY_ACCOUNT.private_key)}\ny",
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_sign_many_from_file_with_alias_successful(
    tmp_path_factory: pytest.TempPathFactory, mock_keyring: dict[str, str]
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {"alias": alias_name, "address": DUMMY_ACCOUNT.address, "private_key": DUMMY_ACCOUNT.private_key}
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])
    _generate_dummy_txn(DUMMY_ACCOUNT.address)
    transaction.write_to_file(  # type: ignore[no-untyped-call]
        [
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 1),
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 2),
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 3),
        ],
        str(cwd / "dummy.txns"),
    )

    # Act
    result = invoke(f"task sign -a {alias_name} --file dummy.txns", input="y", cwd=cwd)

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_sign_many_from_file_with_address_successful(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    _generate_dummy_txn(DUMMY_ACCOUNT.address)
    transaction.write_to_file(  # type: ignore[no-untyped-call]
        [
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 1),
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 2),
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 3),
        ],
        str(cwd / "dummy.txns"),
    )

    # Act
    result = invoke(
        f"task sign -a {DUMMY_ACCOUNT.address} --file dummy.txns",
        input=f"{_get_mnemonic_from_private_key(DUMMY_ACCOUNT.private_key)}\ny",
        cwd=cwd,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_mutually_exclusive_options() -> None:
    # Arrange
    _generate_dummy_txn(DUMMY_ACCOUNT.address)

    # Act
    result = invoke(
        f"task sign -a {DUMMY_ACCOUNT.address} --file dummy.txns --transaction dummy.txn",
        input=f"{_get_mnemonic_from_private_key(DUMMY_ACCOUNT.private_key)}\ny",
    )

    # Assert
    assert result.exit_code == click.exceptions.UsageError.exit_code
    verify(result.output)


def test_file_decoding_errors(tmp_path_factory: pytest.TempPathFactory) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "dummy.txns").touch()

    # Act
    result = invoke(
        f"task sign -a {DUMMY_ACCOUNT.address} --file dummy.txns",
        input=f"{_get_mnemonic_from_private_key(DUMMY_ACCOUNT.private_key)}\ny",
        cwd=cwd,
    )

    # Assert
    assert result.exit_code == 1
    verify(result.output)


def test_transaction_decoding_errors() -> None:
    # Act
    result = invoke(
        f"task sign -a {DUMMY_ACCOUNT.address} --transaction dummy",
        input=f"{_get_mnemonic_from_private_key(DUMMY_ACCOUNT.private_key)}\ny",
    )

    # Assert
    assert result.exit_code == 1
    verify(result.output)
