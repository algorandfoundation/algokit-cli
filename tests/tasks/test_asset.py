import json

from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from algosdk import account, mnemonic
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def _generate_account() -> tuple[str, str]:
    pk, addr = account.generate_account()  # type: ignore[no-untyped-call]
    return pk, addr


def _get_mnemonic_from_private_key(private_key: str) -> str:
    return str(mnemonic.from_private_key(private_key))  # type: ignore[no-untyped-call]


def test_opt_in_no_args() -> None:
    result = invoke("task opt-in")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_in_invalid_network() -> None:
    _, addr = _generate_account()
    asset_id = 123
    result = invoke(f"task opt-in {addr} {asset_id}  --network invalid-network")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_in_to_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_in", return_value={123: "dummy_txn_id"})
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    mocker.patch("algokit.cli.tasks.assets.validate_account_balance_to_opt_in")
    dummy_account_pk, dummy_account_address = _generate_account()
    asset_id = 123
    result = invoke(
        f"task opt-in -a {dummy_account_address} {asset_id} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_in_of_assets_from_account_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_in", return_value={123: "dummy_txn_id"})
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    mocker.patch("algokit.cli.tasks.assets.validate_account_balance_to_opt_in")
    dummy_account_pk, dummy_account_address = _generate_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {"alias": alias_name, "address": dummy_account_address, "private_key": dummy_account_pk}
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    result = invoke(
        f"task opt-in -a {alias_name} {123} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_in_to_assets_from_account_address_failed(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_in", side_effect=Exception("dummy error"))
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    mocker.patch("algokit.cli.tasks.assets.validate_account_balance_to_opt_in")
    dummy_account_pk, dummy_account_address = _generate_account()
    asset_id = 123
    result = invoke(
        f"task opt-in -a {dummy_account_address} {asset_id} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 1
    verify(result.output)


def test_opt_out_no_args() -> None:
    result = invoke("task opt-out")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_out_invalid_network() -> None:
    _, addr = _generate_account()
    asset_id = 123
    result = invoke(f"task opt-out {asset_id} {addr}  --network invalid-network")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_out_of_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_out", return_value={123: "dummy_txn_id"})
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address = _generate_account()
    asset_id = 123
    result = invoke(
        f"task opt-out -a {dummy_account_address} {asset_id} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_of_all_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    dummy_account_info = {"assets": [{"asset-id": 1, "amount": 0}]}
    mocker.patch("algokit.cli.tasks.assets.get_account_info", return_value=dummy_account_info)
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    mocker.patch("algokit.cli.tasks.assets.opt_out", return_value={123: "dummy_txn_id"})
    dummy_account_pk, dummy_account_address = _generate_account()
    result = invoke(
        f"task opt-out -a {dummy_account_address} --network localnet --all",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_of_assets_from_account_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_out", return_value={123: "dummy_txn_id"})
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address = _generate_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {"alias": alias_name, "address": dummy_account_address, "private_key": dummy_account_pk}
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    result = invoke(
        f"task opt-out -a {alias_name} 123 --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_assets_from_account_address_failed(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_out", side_effect=Exception("dummy error"))
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address = _generate_account()
    asset_id = 123
    result = invoke(
        f"task opt-out -a {dummy_account_address} {asset_id} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 1
    verify(result.output)
