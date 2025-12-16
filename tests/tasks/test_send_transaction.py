import base64
import json
from pathlib import Path
from typing import cast

import click
import pytest
from algokit_transact import (
    PaymentTransactionFields,
    SignedTransaction,
    Transaction,
    TransactionType,
    decode_signed_transaction,
    encode_signed_transaction,
    group_transactions,
    make_basic_account_transaction_signer,
)
from pytest_mock import MockerFixture

from tests.tasks.conftest import DUMMY_ACCOUNT, DUMMY_SUGGESTED_PARAMS
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def _write_signed_transactions_to_file(signed_txns: list[SignedTransaction], file_path: Path) -> None:
    """Write signed transactions to a file in msgpack format.

    This mimics the behavior of algosdk's transaction.write_to_file() but uses
    algokit_transact's encode_signed_transaction.
    """
    with file_path.open("wb") as f:
        for stx in signed_txns:
            f.write(encode_signed_transaction(stx))


def _generate_dummy_signed_txn(*, amount: int = 1, encode: bool = False) -> SignedTransaction | str:
    # Create unsigned transaction
    unsigned_txn = Transaction(
        transaction_type=TransactionType.Payment,
        sender=DUMMY_ACCOUNT.address,
        first_valid=DUMMY_SUGGESTED_PARAMS.first_valid,
        last_valid=DUMMY_SUGGESTED_PARAMS.last_valid,
        fee=DUMMY_SUGGESTED_PARAMS.fee,
        genesis_hash=DUMMY_SUGGESTED_PARAMS.genesis_hash,
        genesis_id=DUMMY_SUGGESTED_PARAMS.genesis_id,
        payment=PaymentTransactionFields(
            receiver=DUMMY_ACCOUNT.address,
            amount=amount,
            close_remainder_to=None,
        ),
    )

    # Sign the transaction
    signer = make_basic_account_transaction_signer(DUMMY_ACCOUNT.private_key)
    signed_txn_bytes = signer([unsigned_txn], [0])[0]

    if encode:
        # Return base64-encoded string for CLI input
        return base64.b64encode(signed_txn_bytes).decode()

    # Decode back to SignedTransaction object if not encoding
    return decode_signed_transaction(signed_txn_bytes)


def _generate_dummy_signed_txn_group() -> list[SignedTransaction]:
    # Create unsigned transactions
    txns = [
        Transaction(
            transaction_type=TransactionType.Payment,
            sender=DUMMY_ACCOUNT.address,
            first_valid=DUMMY_SUGGESTED_PARAMS.first_valid,
            last_valid=DUMMY_SUGGESTED_PARAMS.last_valid,
            fee=DUMMY_SUGGESTED_PARAMS.fee if i != 0 else 3000,
            genesis_hash=DUMMY_SUGGESTED_PARAMS.genesis_hash,
            genesis_id=DUMMY_SUGGESTED_PARAMS.genesis_id,
            payment=PaymentTransactionFields(
                receiver=DUMMY_ACCOUNT.address,
                amount=i,
                close_remainder_to=None,
            ),
        )
        for i in range(3)
    ]

    # Group the transactions
    grouped_txns = group_transactions(txns)

    # Sign all transactions
    signer = make_basic_account_transaction_signer(DUMMY_ACCOUNT.private_key)
    signed_txn_bytes_list = signer(grouped_txns, list(range(len(grouped_txns))))

    # Decode back to SignedTransaction objects
    from algokit_transact import decode_signed_transaction

    return [decode_signed_transaction(stx_bytes) for stx_bytes in signed_txn_bytes_list]


def test_send_atomic_txn_group_successful(tmp_path_factory: pytest.TempPathFactory, mocker: MockerFixture) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    txns = _generate_dummy_signed_txn_group()
    _write_signed_transactions_to_file(txns, cwd / "dummy.txns")

    algod_mock = mocker.MagicMock()
    algod_mock.send_raw_transaction.return_value = mocker.MagicMock(tx_id="dummy_tx_id")
    mocker.patch("algokit.cli.tasks.send_transaction.load_algod_client", return_value=algod_mock)

    # Act
    result = invoke("task send --file dummy.txns", input="y", cwd=cwd)

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_send_from_transaction_successful(mocker: MockerFixture) -> None:
    # Arrange
    algod_mock = mocker.MagicMock()
    algod_mock.send_raw_transaction.return_value = mocker.MagicMock(tx_id="dummy_tx_id")
    mocker.patch("algokit.cli.tasks.send_transaction.load_algod_client", return_value=algod_mock)

    # Act
    result = invoke(f"task send --transaction {_generate_dummy_signed_txn(encode=True)}")

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_send_from_file_successful(
    mocker: MockerFixture,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")

    signed_txns = [cast("SignedTransaction", _generate_dummy_signed_txn(amount=i)) for i in range(20)]
    _write_signed_transactions_to_file(signed_txns, cwd / "dummy.txns")

    algod_mock = mocker.MagicMock()
    algod_mock.send_raw_transaction.side_effect = [mocker.MagicMock(tx_id=f"dummy_tx_id_{i}") for i in range(20)]
    mocker.patch("algokit.cli.tasks.send_transaction.load_algod_client", return_value=algod_mock)

    # Act
    result = invoke("task send --file dummy.txns", cwd=cwd)

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_send_from_piped_input_successful(
    mocker: MockerFixture,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Arrange
    tmp_path_factory.mktemp("cwd")

    ## Below simulates stdout from algokit sign transaction
    txns = [{"content": _generate_dummy_signed_txn(amount=i, encode=True), "transaction_id": str(i)} for i in range(20)]

    algod_mock = mocker.MagicMock()
    algod_mock.send_raw_transaction.side_effect = [mocker.MagicMock(tx_id=f"dummy_tx_id_{i}") for i in range(20)]
    mocker.patch("algokit.cli.tasks.send_transaction.load_algod_client", return_value=algod_mock)
    mocker.patch("algokit.cli.tasks.send_transaction.stdin_has_content", return_value=True)

    # Act
    result = invoke("task send ", input=json.dumps(txns))

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_mutually_exclusive_options() -> None:
    # Act
    result = invoke(
        "task send --file dummy.txns --transaction dummy.txn",
    )

    # Assert
    assert result.exit_code == click.exceptions.UsageError.exit_code
    verify(result.output)


def test_file_decoding_no_txn_error(tmp_path_factory: pytest.TempPathFactory) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "dummy.txns").touch()

    # Act
    result = invoke(
        "task send --file dummy.txns",
        cwd=cwd,
    )

    # Assert
    assert result.exit_code == 1
    verify(result.output)


def test_decoding_error(tmp_path_factory: pytest.TempPathFactory) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / "dummy.txns").write_text("dummy")

    # Act
    result = invoke(
        "task send --file dummy.txns",
        cwd=cwd,
    )

    # Assert
    assert result.exit_code == 1
    verify(result.output)
