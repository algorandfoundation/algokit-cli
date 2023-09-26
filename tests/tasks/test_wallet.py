import json
import typing

import algosdk
import pytest
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.fixture()
def mock_keyring(mocker: MockerFixture) -> typing.Generator[dict[str, str | None], None, None]:
    credentials: dict[str, str | None] = {}

    def _get_password(service_name: str, username: str) -> str | None:  # noqa: ARG001
        return credentials[username]

    def _set_password(service_name: str, username: str, password: str) -> None:  # noqa: ARG001
        credentials[username] = password

    def _delete_password(service_name: str, username: str) -> None:  # noqa: ARG001
        credentials[username] = None

    mocker.patch("keyring.get_password", side_effect=_get_password)
    mocker.patch("keyring.set_password", side_effect=_set_password)
    mocker.patch("keyring.delete_password", side_effect=_delete_password)

    yield credentials

    # Teardown step: reset the credentials
    for key in credentials:
        credentials[key] = None


class TestAddAlias:
    def test_wallet_add_address_successful(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        address = algosdk.account.generate_account()[1]  # type: ignore[no-untyped-call]

        # Act
        result = invoke(f"task wallet add {alias_name} -a {address}")

        # Assert
        assert result.exit_code == 0
        assert json.loads(str(mock_keyring[alias_name])) == {
            "alias": alias_name,
            "address": address,
            "private_key": None,
        }

        verify(result.output)

    def test_wallet_add_account_successful(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        pk, address = algosdk.account.generate_account()  # type: ignore[no-untyped-call]
        mnemonic = algosdk.mnemonic.from_private_key(pk)  # type: ignore[no-untyped-call]

        # Act
        result = invoke(f"task wallet add {alias_name} -a {address} -m", input=f"{mnemonic}\n")

        # Assert
        assert result.exit_code == 0
        assert json.loads(str(mock_keyring[alias_name])) == {"alias": alias_name, "address": address, "private_key": pk}

        verify(result.output)

    def test_wallet_add_invalid_address(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        address = "invalid_address"

        # Act
        result = invoke(f"task wallet add {alias_name} -a {address}")

        # Assert
        assert result.exit_code == 1
        assert alias_name not in mock_keyring

        verify(result.output)

    def test_wallet_add_alias_exists(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        bob_alias = "test_alias"
        bob_address = algosdk.account.generate_account()[1]  # type: ignore[no-untyped-call]
        mock_keyring[bob_alias] = json.dumps({"alias": bob_alias, "address": bob_address, "private_key": None})
        alice_address = algosdk.account.generate_account()[1]  # type: ignore[no-untyped-call]

        # Act
        result = invoke(f"task wallet add {bob_alias} -a {alice_address}", input="y\n")

        # Assert
        assert result.exit_code == 0
        assert json.loads(str(mock_keyring[bob_alias])) == {
            "alias": bob_alias,
            "address": alice_address,
            "private_key": None,
        }

        verify(result.output)

    def test_wallet_add_alias_mnemonic_differs(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        address = algosdk.account.generate_account()[1]  # type: ignore[no-untyped-call]
        pk = algosdk.account.generate_account()[0]  # type: ignore[no-untyped-call]
        mnemonic = algosdk.mnemonic.from_private_key(pk)  # type: ignore[no-untyped-call]

        # Act
        result = invoke(f"task wallet add {alias_name} -a {address} -m", input=f"{mnemonic}\n")

        # Assert
        assert result.exit_code == 0
        assert json.loads(str(mock_keyring[alias_name])) == {"alias": alias_name, "address": address, "private_key": pk}

        verify(result.output)
