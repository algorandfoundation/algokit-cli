import json

from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from algosdk import account, mnemonic
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


class OptMock:
    def get_asset_id(self) -> int:
        return 1234


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
    asset_id = OptMock().get_asset_id()
    result = invoke(f"task opt-in {asset_id} {addr}  --network invalid-network")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_in_invalid_account() -> None:
    invalid_account = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    asset_id = OptMock().get_asset_id()
    dummy_account_pk, _ = _generate_account()
    result = invoke(
        f"task opt-in {asset_id} {invalid_account} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code != 0
    verify(result.output)


def test_opt_in_invalid_asset_id() -> None:
    dummy_account_pk, dummy_account_address = _generate_account()
    asset_id = "1234"
    result = invoke(
        f"task opt-in {asset_id} {dummy_account_address} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    # Assert
    assert result.exit_code != 0
    verify(result.output)


def test_opt_in_to_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_in")
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address = _generate_account()
    asset_id = OptMock().get_asset_id()
    result = invoke(
        f"task opt-in {asset_id} {dummy_account_address} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_in_of_assets_from_account_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_in")
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_sender_pk, dummy_sender_address = _generate_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {"alias": alias_name, "address": dummy_sender_address, "private_key": dummy_sender_pk}
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    result = invoke(
        f"task opt-in {OptMock().get_asset_id()} {alias_name} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_sender_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_no_args() -> None:
    result = invoke("task opt-out")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_out_invalid_network() -> None:
    _, addr = _generate_account()
    asset_id = OptMock().get_asset_id()
    result = invoke(f"task opt-out {asset_id} {addr}  --network invalid-network")

    assert result.exit_code != 0
    verify(result.output)


def test_opt_out_invalid_account() -> None:
    invalid_account = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    asset_id = OptMock().get_asset_id()
    dummy_account_pk, _ = _generate_account()
    result = invoke(
        f"task opt-out  {invalid_account} {asset_id} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code != 0
    verify(result.output)


def test_opt_out_of_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_out")
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address = _generate_account()
    asset_id = OptMock().get_asset_id()
    result = invoke(
        f"task opt-out {dummy_account_address} {asset_id} --network localnet",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_of_all_assets_from_account_address_successful(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_out")
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_account_pk, dummy_account_address = _generate_account()
    result = invoke(
        f"task opt-out {dummy_account_address} --network localnet --all",
        input=_get_mnemonic_from_private_key(dummy_account_pk),
    )

    assert result.exit_code == 0
    verify(result.output)


def test_opt_out_of_assets_from_account_alias_successful(mocker: MockerFixture, mock_keyring: dict[str, str]) -> None:
    mocker.patch("algokit.cli.tasks.assets.opt_out")
    mocker.patch("algokit.cli.tasks.assets.validate_address")
    dummy_sender_pk, dummy_sender_address = _generate_account()

    alias_name = "dummy_alias"
    mock_keyring[alias_name] = json.dumps(
        {"alias": alias_name, "address": dummy_sender_address, "private_key": dummy_sender_pk}
    )
    mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

    result = invoke(
        f"task opt-out {alias_name} {OptMock().get_asset_id()}  --network localnet",
        input=_get_mnemonic_from_private_key(dummy_sender_pk),
    )

    assert result.exit_code == 0
    verify(result.output)
