import json

import click
import pytest
from algosdk import encoding, transaction
from pytest_mock import MockerFixture

from tests.tasks.conftest import DUMMY_ACCOUNT, DUMMY_SUGGESTED_PARAMS
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def _generate_dummy_signed_txn(*, amount: int = 1, encode: bool = False) -> transaction.SignedTransaction | str:
    unsigned_txn = transaction.PaymentTxn(  # type: ignore[no-untyped-call]
        DUMMY_ACCOUNT.address, DUMMY_SUGGESTED_PARAMS, DUMMY_ACCOUNT.address, amt=amount
    )
    txn = unsigned_txn.sign(DUMMY_ACCOUNT.private_key)  # type: ignore[no-untyped-call]

    if encode:
        return str(encoding.msgpack_encode(txn))  # type: ignore[no-untyped-call]

    return txn  # type: ignore[no-any-return]


def _generate_dummy_signed_txn_group() -> list[transaction.SignedTransaction]:
    txns = [
        transaction.PaymentTxn(DUMMY_ACCOUNT.address, DUMMY_SUGGESTED_PARAMS, DUMMY_ACCOUNT.address, amt=i)  # type: ignore[no-untyped-call]
        for i in range(3)
    ]
    txns[0].fee = 3000

    gid = transaction.calculate_group_id(txns)  # type: ignore[no-untyped-call]
    signed_txns = []
    for txn in txns:
        txn.group = gid
        signed_txns.append(txn.sign(DUMMY_ACCOUNT.private_key))  # type: ignore[no-untyped-call]

    return signed_txns


def test_send_atomic_txn_group_successful(tmp_path_factory: pytest.TempPathFactory, mocker: MockerFixture) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    txns = _generate_dummy_signed_txn_group()
    transaction.write_to_file(txns, str(cwd / "dummy.txns"))  # type: ignore[no-untyped-call]

    algod_mock = mocker.MagicMock()
    algod_mock.send_transactions.return_value = "dummy_tx_id"
    mocker.patch("algokit.cli.tasks.send_transaction.load_algod_client", return_value=algod_mock)

    # Act
    result = invoke("task send --file dummy.txns", input="y", cwd=cwd)

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_send_from_transaction_successful(mocker: MockerFixture) -> None:
    # Arrange
    algod_mock = mocker.MagicMock()
    algod_mock.send_transaction.return_value = "dummy_tx_id"
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

    transaction.write_to_file(  # type: ignore[no-untyped-call]
        [_generate_dummy_signed_txn(amount=i) for i in range(20)],
        str(cwd / "dummy.txns"),
    )

    algod_mock = mocker.MagicMock()
    algod_mock.send_transaction.side_effect = [f"dummy_tx_id_{i}" for i in range(20)]
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
    algod_mock.send_transaction.side_effect = [f"dummy_tx_id_{i}" for i in range(20)]
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
