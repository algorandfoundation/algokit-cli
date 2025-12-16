import base64
import json

import pytest
from algokit_common import address_from_public_key
from algokit_utils.algo25 import secret_key_to_mnemonic
from nacl.signing import SigningKey
from pytest_mock import MockerFixture

from algokit.core.tasks.wallet import WALLET_ALIASES_KEYRING_USERNAME
from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def generate_test_account() -> tuple[str, str]:
    """Generate a test account for testing purposes.

    Returns:
        tuple[str, str]: A tuple of (private_key, address).
            The private key is base64-encoded (64 bytes: 32 bytes secret + 32 bytes public key).
    """
    signing_key = SigningKey.generate()
    private_key_bytes = signing_key.encode() + signing_key.verify_key.encode()
    private_key = base64.b64encode(private_key_bytes).decode()
    address = address_from_public_key(signing_key.verify_key.encode())
    return private_key, address


class TestAddAlias:
    def test_wallet_add_address_successful(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        address = generate_test_account()[1]

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
        pk, address = generate_test_account()
        mnemonic = secret_key_to_mnemonic(base64.b64decode(pk))

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
        bob_address = generate_test_account()[1]
        mock_keyring[bob_alias] = json.dumps({"alias": bob_alias, "address": bob_address, "private_key": None})
        alice_address = generate_test_account()[1]

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
        address = generate_test_account()[1]
        pk = generate_test_account()[0]
        mnemonic = secret_key_to_mnemonic(base64.b64decode(pk))

        # Act
        result = invoke(f"task wallet add {alias_name} -a {address} -m", input=f"{mnemonic}\n")

        # Assert
        assert result.exit_code == 0
        assert json.loads(str(mock_keyring[alias_name])) == {"alias": alias_name, "address": address, "private_key": pk}

        verify(result.output)

    def test_wallet_add_alias_limit_error(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        dummy_aliases = []
        for i in range(50):
            alias_name = f"test_alias_{i}"
            dummy_aliases.append(alias_name)
            address = generate_test_account()[1]
            mock_keyring[alias_name] = json.dumps({"alias": alias_name, "address": address, "private_key": None})
        mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps(dummy_aliases)

        alias_name = "test_alias"
        address = generate_test_account()[1]

        # Act
        result = invoke(f"task wallet add {alias_name} -a {address}")

        # Assert
        assert result.exit_code == 1
        assert alias_name not in mock_keyring

        verify(result.output)

    def test_wallet_add_alias_generic_error(self, mocker: MockerFixture, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        address = generate_test_account()[1]
        mocker.patch("algokit.cli.tasks.wallet.add_alias", side_effect=Exception("test error"))

        # Act
        result = invoke(f"task wallet add {alias_name} -a {address}")

        # Assert
        assert result.exit_code == 1
        assert alias_name not in mock_keyring

        verify(result.output)


class TestGetAlias:
    def test_wallet_get_address_alias_successful(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        address = generate_test_account()[1]
        mock_keyring[alias_name] = json.dumps({"alias": alias_name, "address": address, "private_key": None})

        # Act
        result = invoke(f"task wallet get {alias_name}")

        # Assert
        assert result.exit_code == 0
        assert result.output == f"Address for alias `{alias_name}`: {address}\n"

    def test_wallet_get_account_alias_successful(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        pk, address = generate_test_account()
        mock_keyring[alias_name] = json.dumps({"alias": alias_name, "address": address, "private_key": pk})

        # Act
        result = invoke(f"task wallet get {alias_name}")

        # Assert
        assert result.exit_code == 0
        assert result.output == f"Address for alias `{alias_name}`: {address} (🔐 includes private key)\n"

    @pytest.mark.usefixtures("mock_keyring")
    def test_wallet_get_alias_not_found(
        self,
    ) -> None:
        # Arrange
        alias_name = "test_alias"

        # Act
        result = invoke(f"task wallet get {alias_name}")

        # Assert
        assert result.exit_code == 1
        verify(result.output)


class TestListAliases:
    def test_wallet_list_aliases_successful(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        mock_keyring["test_alias_1"] = json.dumps(
            {"alias": "test_alias_1", "address": "test_address_1", "private_key": None},
        )
        mock_keyring["test_alias_2"] = json.dumps(
            {
                "alias": "test_alias_2",
                "address": "test_address_2",
                "private_key": "blabla",
            }
        )
        mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps(["test_alias_1", "test_alias_2"])

        # Act
        result = invoke("task wallet list")

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    @pytest.mark.usefixtures("mock_keyring")
    def test_wallet_list_aliases_not_found(self) -> None:
        # Arrange

        # Act
        result = invoke("task wallet list")

        # Assert
        assert result.exit_code == 0
        verify(result.output)


class TestRemoveAlias:
    def test_wallet_remove_alias_successful(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        alias_name = "test_alias"
        address = generate_test_account()[1]
        mock_keyring[alias_name] = json.dumps({"alias": alias_name, "address": address, "private_key": None})
        mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps([alias_name])

        # Act
        result = invoke(f"task wallet remove {alias_name}", input="y\n")

        # Assert
        assert result.exit_code == 0
        assert alias_name not in mock_keyring

        verify(result.output)

    @pytest.mark.usefixtures("mock_keyring")
    def test_wallet_remove_alias_not_found(self) -> None:
        # Arrange
        alias_name = "test_alias"

        # Act
        result = invoke(f"task wallet remove {alias_name}")

        # Assert
        assert result.exit_code == 1
        verify(result.output)

    @pytest.mark.usefixtures("mock_keyring")
    def test_wallet_remove_alias_generic_error(self, mocker: MockerFixture) -> None:
        # Arrange
        alias_name = "test_alias"
        mocker.patch("algokit.cli.tasks.wallet.remove_alias", side_effect=Exception("test error"))

        # Act
        result = invoke(f"task wallet remove {alias_name}")

        # Assert
        assert result.exit_code == 1
        verify(result.output)


class TestResetAliases:
    def test_wallet_reset_aliases_successful(self, mock_keyring: dict[str, str | None]) -> None:
        # Arrange
        mock_keyring["test_alias_1"] = json.dumps(
            {"alias": "test_alias_1", "address": "test_address_1", "private_key": None},
        )
        mock_keyring["test_alias_2"] = json.dumps(
            {
                "alias": "test_alias_2",
                "address": "test_address_2",
                "private_key": "blabla",
            }
        )
        mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps(["test_alias_1", "test_alias_2"])

        # Act
        result = invoke("task wallet reset", input="y\n")

        # Assert
        assert result.exit_code == 0
        assert mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] == "[]"

        verify(result.output)

    @pytest.mark.usefixtures("mock_keyring")
    def test_wallet_reset_aliases_not_found(self) -> None:
        # Arrange

        # Act
        result = invoke("task wallet reset")

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    def test_wallet_reset_aliases_generic_error(
        self, mocker: MockerFixture, mock_keyring: dict[str, str | None]
    ) -> None:
        # Arrange
        mock_keyring[WALLET_ALIASES_KEYRING_USERNAME] = json.dumps(["test_alias_1"])
        mock_keyring["test_alias_1"] = json.dumps(
            {"alias": "test_alias_1", "address": "test_address_1", "private_key": None},
        )
        mocker.patch("algokit.cli.tasks.wallet.remove_alias", side_effect=Exception("test error"))

        # Act
        result = invoke("task wallet reset", input="y\n")

        # Assert
        assert result.exit_code == 1
        verify(result.output)
