import json

import pytest
from algokit_utils import SendTransactionComposerResults
from pytest_mock import MockerFixture

from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from tests.conftest import generate_test_account
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


class TransactionMock:
    def get_txid(self) -> str:
        return "dummy_txid"


def test_transfer_no_args() -> None:
    result = invoke("task transfer")

    assert result.exit_code != 0
    verify(result.output)


@pytest.mark.usefixtures("mock_keyring")
def test_transfer_invalid_sender_account() -> None:
    # Arrange
    _, dummy_receiver, _ = generate_test_account()

    # Act
    result = invoke(f"task transfer -s invalid-address -r {dummy_receiver} -a 1")

    # Assert
    assert result.exit_code != 0
    verify(result.output)


@pytest.mark.usefixtures("mock_keyring")
def test_transfer_invalid_receiver_account() -> None:
    # Arrange
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()

    # Act
    result = invoke(
        f"task transfer -s {dummy_sender_address} -r invalid-address -a 1",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code != 0
    verify(result.output)


def test_transfer_no_amount() -> None:
    # Arrange
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()
    _, dummy_receiver_address, _ = generate_test_account()

    # Act
    result = invoke(
        f"task transfer -s {dummy_sender_address} -r {dummy_receiver_address}",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code != 0
    verify(result.output)


def test_transfer_algo_from_address_successful(mocker: MockerFixture) -> None:
    # Arrange
    algorand_mock = mocker.MagicMock()
    composer_mock = mocker.MagicMock()
    composer_mock.add_payment.return_value = composer_mock
    composer_mock.send.return_value = SendTransactionComposerResults(
        group_id="dummy_group_id",
        confirmations=[],
        tx_ids=["dummy_txid"],
        transactions=[],
        returns=[],
    )
    algorand_mock.new_group.return_value = composer_mock
    mocker.patch("algokit.cli.tasks.transfer.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.transfer.validate_address")
    mocker.patch("algokit.cli.tasks.transfer.validate_balance")
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()
    _, dummy_receiver_address, _ = generate_test_account()

    # Act
    result = invoke(
        f"task transfer -s {dummy_sender_address} -r {dummy_receiver_address} -a 1",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_transfer_algo_from_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    # Arrange
    algorand_mock = mocker.MagicMock()
    composer_mock = mocker.MagicMock()
    composer_mock.add_payment.return_value = composer_mock
    composer_mock.send.return_value = SendTransactionComposerResults(
        group_id="dummy_group_id",
        confirmations=[],
        tx_ids=["dummy_txid"],
        transactions=[],
        returns=[],
    )
    algorand_mock.new_group.return_value = composer_mock
    mocker.patch("algokit.cli.tasks.transfer.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.transfer.validate_address")
    mocker.patch("algokit.cli.tasks.transfer.validate_balance")
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()
    _, dummy_receiver_address, _ = generate_test_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {
            "alias": alias_name,
            "address": dummy_sender_address,
            "private_key": dummy_sender_pk,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    # Act
    result = invoke(
        f"task transfer -s {alias_name} -r {dummy_receiver_address} -a 1",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_transfer_asset_from_address_successful(mocker: MockerFixture) -> None:
    # Arrange
    algorand_mock = mocker.MagicMock()
    composer_mock = mocker.MagicMock()
    composer_mock.add_asset_transfer.return_value = composer_mock
    composer_mock.send.return_value = SendTransactionComposerResults(
        group_id="dummy_group_id",
        confirmations=[],
        tx_ids=["dummy_txid"],
        transactions=[],
        returns=[],
    )
    algorand_mock.new_group.return_value = composer_mock
    mocker.patch("algokit.cli.tasks.transfer.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.transfer.validate_address")
    mocker.patch("algokit.cli.tasks.transfer.validate_balance")
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()
    _, dummy_receiver_address, _ = generate_test_account()

    # Act
    result = invoke(
        f"task transfer -s {dummy_sender_address} -r {dummy_receiver_address} -a 1 --id 1234",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_transfer_asset_from_address_to_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    # Arrange
    algorand_mock = mocker.MagicMock()
    composer_mock = mocker.MagicMock()
    composer_mock.add_asset_transfer.return_value = composer_mock
    composer_mock.send.return_value = SendTransactionComposerResults(
        group_id="dummy_group_id",
        confirmations=[],
        tx_ids=["dummy_txid"],
        transactions=[],
        returns=[],
    )
    algorand_mock.new_group.return_value = composer_mock
    mocker.patch("algokit.cli.tasks.transfer.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.transfer.validate_address")
    mocker.patch("algokit.cli.tasks.transfer.validate_balance")
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()

    dummy_receiver_alias = "dummy_receiver_alias"
    mock_keyring[dummy_receiver_alias] = json.dumps(
        {
            "alias": dummy_receiver_alias,
            "address": dummy_sender_address,
            "private_key": None,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([dummy_receiver_alias])

    # Act
    result = invoke(
        f"task transfer -s {dummy_sender_address} -r {dummy_receiver_alias} -a 1 --id 1234",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_transfer_asset_from_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    # Arrange
    algorand_mock = mocker.MagicMock()
    composer_mock = mocker.MagicMock()
    composer_mock.add_asset_transfer.return_value = composer_mock
    composer_mock.send.return_value = SendTransactionComposerResults(
        group_id="dummy_group_id",
        confirmations=[],
        tx_ids=["dummy_txid"],
        transactions=[],
        returns=[],
    )
    algorand_mock.new_group.return_value = composer_mock
    mocker.patch("algokit.cli.tasks.transfer.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.transfer.validate_address")
    mocker.patch("algokit.cli.tasks.transfer.validate_balance")
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()
    _, dummy_receiver_address, _ = generate_test_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {
            "alias": alias_name,
            "address": dummy_sender_address,
            "private_key": dummy_sender_pk,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    # Act
    result = invoke(
        f"task transfer -s {alias_name} -r {dummy_receiver_address} -a 1 --id 1234",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_transfer_failed(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    # Arrange
    algorand_mock = mocker.MagicMock()
    algorand_mock.new_group.return_value = mocker.MagicMock(
        add_payment=mocker.MagicMock(side_effect=Exception("dummy error"))
    )
    mocker.patch("algokit.cli.tasks.transfer.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.transfer.validate_address")
    mocker.patch("algokit.cli.tasks.transfer.validate_balance")
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()
    _, dummy_receiver_address, _ = generate_test_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {
            "alias": alias_name,
            "address": dummy_sender_address,
            "private_key": dummy_sender_pk,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    # Act
    result = invoke(
        f"task transfer -s {alias_name} -r {dummy_receiver_address} -a 1",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code == 1
    verify(result.output)


def test_transfer_on_testnet(mocker: MockerFixture) -> None:
    # Arrange
    algorand_mock = mocker.MagicMock()
    composer_mock = mocker.MagicMock()
    composer_mock.add_payment.return_value = composer_mock
    composer_mock.send.return_value = SendTransactionComposerResults(
        group_id="dummy_group_id",
        confirmations=[],
        tx_ids=["dummy_txid"],
        transactions=[],
        returns=[],
    )
    algorand_mock.new_group.return_value = composer_mock
    mocker.patch("algokit.cli.tasks.transfer.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.transfer.validate_address")
    mocker.patch("algokit.cli.tasks.transfer.validate_balance")
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()
    _, dummy_receiver_address, _ = generate_test_account()

    # Act
    result = invoke(
        f"task transfer -s {dummy_sender_address} -r {dummy_receiver_address} -a 1 -n testnet",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_transfer_on_mainnet(mocker: MockerFixture) -> None:
    # Arrange
    algorand_mock = mocker.MagicMock()
    composer_mock = mocker.MagicMock()
    composer_mock.add_payment.return_value = composer_mock
    composer_mock.send.return_value = SendTransactionComposerResults(
        group_id="dummy_group_id",
        confirmations=[],
        tx_ids=["dummy_txid"],
        transactions=[],
        returns=[],
    )
    algorand_mock.new_group.return_value = composer_mock
    mocker.patch("algokit.cli.tasks.transfer.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.transfer.validate_address")
    mocker.patch("algokit.cli.tasks.transfer.validate_balance")
    dummy_sender_pk, dummy_sender_address, dummy_sender_mnemonic = generate_test_account()
    _, dummy_receiver_address, _ = generate_test_account()

    # Act
    result = invoke(
        f"task transfer -s {dummy_sender_address} -r {dummy_receiver_address} -a 1 -n mainnet",
        input=dummy_sender_mnemonic,
    )

    # Assert
    assert result.exit_code == 0
    verify(result.output)
