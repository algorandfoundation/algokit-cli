import base64
import json
from pathlib import Path

import click
import pytest
from algokit_transact.models.payment import PaymentTransactionFields
from algokit_transact.models.transaction import Transaction, TransactionType
from algokit_utils.algo25 import secret_key_to_mnemonic
from algokit_utils.transact import decode_transactions, encode_transactions, group_transactions

from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from tests.tasks.conftest import DUMMY_ACCOUNT, DUMMY_SUGGESTED_PARAMS
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def _write_transactions_to_file(transactions: list[Transaction], file_path: Path | str) -> None:
    """Write transactions to a file in msgpack format (compatible with algosdk's write_to_file)."""
    encoded_txns = encode_transactions(transactions)
    with Path(file_path).open("wb") as f:
        for encoded_txn in encoded_txns:
            f.write(encoded_txn)


def _read_transactions_from_file(file_path: Path | str) -> list[Transaction]:
    """Read transactions from a file in msgpack format (compatible with algosdk's retrieve_from_file)."""
    import msgpack

    with Path(file_path).open("rb") as f:
        content = f.read()

    # Split the concatenated msgpack messages into individual transaction dicts
    unpacker = msgpack.Unpacker()
    unpacker.feed(content)

    # Collect all top-level msgpack objects (each should be a dict representing a transaction)
    transaction_dicts = []
    for unpacked_obj in unpacker:
        if isinstance(unpacked_obj, dict):
            transaction_dicts.append(unpacked_obj)

    # Re-encode each dict to bytes for decode_transactions
    transaction_bytes = [msgpack.packb(txn_dict) for txn_dict in transaction_dicts]

    # Decode using algokit_utils
    return decode_transactions(transaction_bytes)


def _generate_dummy_txn(sender: str, amount: int = 1) -> Transaction:
    """Generate a dummy payment transaction for testing."""
    return Transaction(
        transaction_type=TransactionType.Payment,
        sender=sender,
        first_valid=DUMMY_SUGGESTED_PARAMS.first_valid,
        last_valid=DUMMY_SUGGESTED_PARAMS.last_valid,
        fee=DUMMY_SUGGESTED_PARAMS.min_fee,
        genesis_id=DUMMY_SUGGESTED_PARAMS.genesis_id,
        genesis_hash=DUMMY_SUGGESTED_PARAMS.genesis_hash,
        payment=PaymentTransactionFields(
            amount=amount,
            receiver=sender,
        ),
    )


def _get_mnemonic_from_private_key(private_key: str) -> str:
    """Convert a private key to a mnemonic phrase.

    Args:
        private_key: Base64-encoded private key string (64 bytes when decoded: 32-byte seed + 32-byte public key)

    Returns:
        25-word mnemonic phrase
    """
    # Decode the base64 string to get the actual bytes
    private_key_bytes = base64.b64decode(private_key)
    return secret_key_to_mnemonic(private_key_bytes)


def test_sign_atomic_txn_group_successful(
    tmp_path_factory: pytest.TempPathFactory, mock_keyring: dict[str, str]
) -> None:
    # Arrange
    cwd = tmp_path_factory.mktemp("cwd")
    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {
            "alias": alias_name,
            "address": DUMMY_ACCOUNT.address,
            "private_key": DUMMY_ACCOUNT.private_key,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])
    txn_a = _generate_dummy_txn(DUMMY_ACCOUNT.address)
    txn_b = _generate_dummy_txn(DUMMY_ACCOUNT.address)
    grouped_txns = group_transactions([txn_a, txn_b])
    _write_transactions_to_file(grouped_txns, cwd / "dummy.txns")

    # Act
    result = invoke(f"task sign -a {alias_name} --file dummy.txns", input="y", cwd=cwd)

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_sign_from_stdin_with_alias_successful(mock_keyring: dict[str, str]) -> None:
    # Arrange
    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {
            "alias": alias_name,
            "address": DUMMY_ACCOUNT.address,
            "private_key": DUMMY_ACCOUNT.private_key,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])
    dummy_txn = _generate_dummy_txn(DUMMY_ACCOUNT.address)

    # Act
    encoded_txns = encode_transactions([dummy_txn])
    txn = base64.b64encode(encoded_txns[0]).decode()
    result = invoke(f"task sign -a {alias_name} --transaction {txn}", input="y")

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_sign_from_stdin_with_address_successful() -> None:
    # Arrange
    dummy_txn = _generate_dummy_txn(DUMMY_ACCOUNT.address)

    # Act
    encoded_txns = encode_transactions([dummy_txn])
    txn = base64.b64encode(encoded_txns[0]).decode()
    result = invoke(
        f"task sign -a {DUMMY_ACCOUNT.address} --transaction {txn}",
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
        {
            "alias": alias_name,
            "address": DUMMY_ACCOUNT.address,
            "private_key": DUMMY_ACCOUNT.private_key,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])
    _generate_dummy_txn(DUMMY_ACCOUNT.address)
    _write_transactions_to_file(
        [
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 1),
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 2),
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 3),
        ],
        cwd / "dummy.txns",
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
    _write_transactions_to_file(
        [
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 1),
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 2),
            _generate_dummy_txn(DUMMY_ACCOUNT.address, 3),
        ],
        cwd / "dummy.txns",
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
