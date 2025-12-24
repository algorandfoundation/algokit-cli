import json

from algokit_algod_client.models import Account, AssetHolding
from algokit_utils import BulkAssetOptInOutResult
from pytest_mock import MockerFixture

from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from tests.conftest import generate_test_account
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def test_opt_in_no_args() -> None:
    result = invoke("task opt-in")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_in_invalid_network() -> None:
    _, addr, _ = generate_test_account()
    asset_id = 123
    result = invoke(f"task opt-in {addr} {asset_id}  --network invalid-network")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_in_to_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    algorand_mock = mocker.MagicMock()
    algorand_mock.asset.bulk_opt_in.return_value = [
        BulkAssetOptInOutResult(asset_id=123, transaction_id="dummy_txn_id")
    ]
    algorand_mock = mocker.patch("algokit.cli.tasks.assets.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    mocker.patch("algokit.cli.tasks.assets.validate_account_balance_to_opt_in")
    dummy_account_pk, dummy_account_address, dummy_account_mnemonic = generate_test_account()
    asset_id = 123
    result = invoke(
        f"task opt-in -a {dummy_account_address} {asset_id} --network localnet",
        input=dummy_account_mnemonic,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_in_of_assets_from_account_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    algorand_mock = mocker.MagicMock()
    algorand_mock.asset.bulk_opt_in.return_value = [
        BulkAssetOptInOutResult(asset_id=123, transaction_id="dummy_txn_id")
    ]
    algorand_mock = mocker.patch("algokit.cli.tasks.assets.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    mocker.patch("algokit.cli.tasks.assets.validate_account_balance_to_opt_in")
    dummy_account_pk, dummy_account_address, dummy_account_mnemonic = generate_test_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {
            "alias": alias_name,
            "address": dummy_account_address,
            "private_key": dummy_account_pk,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    result = invoke(
        f"task opt-in -a {alias_name} {123} --network localnet",
        input=dummy_account_mnemonic,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_in_to_assets_from_account_address_failed(mocker: MockerFixture) -> None:
    algorand_mock = mocker.MagicMock()
    algorand_mock.asset.bulk_opt_in.side_effect = Exception("dummy error")
    algorand_mock = mocker.patch("algokit.cli.tasks.assets.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    mocker.patch("algokit.cli.tasks.assets.validate_account_balance_to_opt_in")
    dummy_account_pk, dummy_account_address, dummy_account_mnemonic = generate_test_account()
    asset_id = 123
    result = invoke(
        f"task opt-in -a {dummy_account_address} {asset_id} --network localnet",
        input=dummy_account_mnemonic,
    )

    assert result.exit_code == 1
    verify(result.output)


def test_opt_out_no_args() -> None:
    result = invoke("task opt-out")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_out_invalid_network() -> None:
    _, addr, _ = generate_test_account()
    asset_id = 123
    result = invoke(f"task opt-out {asset_id} {addr}  --network invalid-network")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_out_of_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    algorand_mock = mocker.MagicMock()
    algorand_mock.asset.bulk_opt_out.return_value = [
        BulkAssetOptInOutResult(asset_id=123, transaction_id="dummy_txn_id")
    ]
    algorand_mock = mocker.patch("algokit.cli.tasks.assets.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address, dummy_account_mnemonic = generate_test_account()
    asset_id = 123
    result = invoke(
        f"task opt-out -a {dummy_account_address} {asset_id} --network localnet",
        input=dummy_account_mnemonic,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_of_all_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    dummy_account_info = Account(assets=[AssetHolding(asset_id=1)])
    mocker.patch("algokit_algod_client.client.AlgodClient.account_information", return_value=dummy_account_info)
    algorand_mock = mocker.MagicMock()
    algorand_mock.asset.bulk_opt_out.return_value = [
        BulkAssetOptInOutResult(asset_id=123, transaction_id="dummy_txn_id")
    ]
    algorand_mock = mocker.patch("algokit.cli.tasks.assets.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address, dummy_account_mnemonic = generate_test_account()
    result = invoke(
        f"task opt-out -a {dummy_account_address} --network localnet --all",
        input=dummy_account_mnemonic,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_of_assets_from_account_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    algorand_mock = mocker.MagicMock()
    algorand_mock.asset.bulk_opt_out.return_value = [
        BulkAssetOptInOutResult(asset_id=123, transaction_id="dummy_txn_id")
    ]
    algorand_mock = mocker.patch("algokit.cli.tasks.assets.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address, dummy_account_mnemonic = generate_test_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {
            "alias": alias_name,
            "address": dummy_account_address,
            "private_key": dummy_account_pk,
        }
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    result = invoke(
        f"task opt-out -a {alias_name} 123 --network localnet",
        input=dummy_account_mnemonic,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_assets_from_account_address_failed(mocker: MockerFixture) -> None:
    algorand_mock = mocker.MagicMock()
    algorand_mock.asset.bulk_opt_out.side_effect = Exception("dummy error")
    algorand_mock = mocker.patch("algokit.cli.tasks.assets.get_algorand_client_for_network", return_value=algorand_mock)
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address, dummy_account_mnemonic = generate_test_account()
    asset_id = 123
    result = invoke(
        f"task opt-out -a {dummy_account_address} {asset_id} --network localnet",
        input=dummy_account_mnemonic,
    )

    assert result.exit_code == 1
    verify(result.output)
