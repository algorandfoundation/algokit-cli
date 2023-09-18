import typing
from pathlib import Path

import click
import httpx
import jwt
import pytest
from algokit.cli.dispenser import DEFAULT_CI_TOKEN_FILENAME, DISPENSER_ASSETS, DispenserAssetName
from algokit.core.dispenser import (
    DISPENSER_KEYRING_ACCESS_TOKEN_KEY,
    DISPENSER_KEYRING_ID_TOKEN_KEY,
    DISPENSER_KEYRING_REFRESH_TOKEN_KEY,
    DISPENSER_KEYRING_USER_ID_KEY,
    ApiConfig,
    APIErrorCode,
    AuthConfig,
)
from approvaltests.namer import NamerFactory
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.fixture(autouse=True)
def _mock_api_base_url(mocker: MockerFixture) -> None:
    mocker.patch("algokit.core.dispenser.ApiConfig.BASE_URL", "https://snapshottest.dispenser.com")


@pytest.fixture()
def mock_keyring(mocker: MockerFixture) -> typing.Generator[dict[str, str | None], None, None]:
    credentials: dict[str, str | None] = {
        DISPENSER_KEYRING_ID_TOKEN_KEY: None,
        DISPENSER_KEYRING_ACCESS_TOKEN_KEY: None,
        DISPENSER_KEYRING_REFRESH_TOKEN_KEY: None,
        DISPENSER_KEYRING_USER_ID_KEY: None,
    }

    def _get_password(namespace: str, key: str) -> str | None:  # noqa: ARG001
        return credentials[key]

    def _set_password(namespace: str, key: str, password: str) -> None:  # noqa: ARG001
        credentials[key] = password

    def _delete_password(namespace: str, key: str) -> None:  # noqa: ARG001
        credentials[key] = None

    mocker.patch("keyring.get_password", side_effect=_get_password)
    mocker.patch("keyring.set_password", side_effect=_set_password)
    mocker.patch("keyring.delete_password", side_effect=_delete_password)

    yield credentials

    # Teardown step: reset the credentials
    for key in credentials:
        credentials[key] = None


def _set_mock_keyring_credentials(
    mock_keyring: dict, id_token: str, access_token: str, refresh_token: str, user_id: str
) -> None:
    mock_keyring[DISPENSER_KEYRING_ID_TOKEN_KEY] = id_token
    mock_keyring[DISPENSER_KEYRING_ACCESS_TOKEN_KEY] = access_token
    mock_keyring[DISPENSER_KEYRING_REFRESH_TOKEN_KEY] = refresh_token
    mock_keyring[DISPENSER_KEYRING_USER_ID_KEY] = user_id


@pytest.fixture()
def cwd(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("cwd")


@pytest.mark.parametrize(
    "command",
    ["logout", "login", "refund", "fund", "limit"],
)
def test_no_internet_access(command: str, mocker: MockerFixture) -> None:
    # Arrange
    is_network_available_mock = mocker.patch("algokit.cli.dispenser.is_network_available", return_value=False)

    # Act
    result = invoke(f"dispenser {command}")

    # Assert
    is_network_available_mock.assert_called()
    assert result.exit_code == 1
    assert result.output == "ERROR: Please connect to internet first\n"


class TestTokenRefresh:
    def test_token_refresh_success(
        self, mock_keyring: dict[str, str | None], mocker: MockerFixture, httpx_mock: HTTPXMock
    ) -> None:
        # Arrange
        _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        mocker.patch("algokit.core.dispenser.jwt.decode", return_value={"sub": "new_user_id"})
        mocker.patch("algokit.core.dispenser._get_access_token_rsa_pub_key")
        httpx_mock.add_response(
            url=AuthConfig.OAUTH_TOKEN_URL,
            method="POST",
            json={
                "access_token": "new_access_token",
                "id_token": "new_id_token",
                "refresh_token": "new_refresh_token",
            },
        )

        # Act
        from algokit.core.dispenser import _refresh_user_access_token

        _refresh_user_access_token()

        # Assert
        assert mock_keyring[DISPENSER_KEYRING_ACCESS_TOKEN_KEY] == "new_access_token"
        assert mock_keyring[DISPENSER_KEYRING_ID_TOKEN_KEY] == "new_id_token"
        assert mock_keyring[DISPENSER_KEYRING_REFRESH_TOKEN_KEY] == "new_refresh_token"
        assert mock_keyring[DISPENSER_KEYRING_USER_ID_KEY] == "new_user_id"

    def test_token_refresh_failure(
        self, mock_keyring: dict[str, str | None], mocker: MockerFixture, httpx_mock: HTTPXMock
    ) -> None:
        # Arrange
        _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        mocker.patch("algokit.core.dispenser._get_access_token_rsa_pub_key")
        httpx_mock.add_exception(httpx.HTTPError("Error response"), url=AuthConfig.OAUTH_TOKEN_URL)

        # Act and Assert
        from algokit.core.dispenser import _refresh_user_access_token

        with pytest.raises(httpx.HTTPError):
            _refresh_user_access_token()


# Snapshot tests for dispenser commands


class TestLogoutCommand:
    def test_logout_command_already_logged_out(self, mocker: MockerFixture) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=False)

        # Act
        result = invoke("dispenser logout")

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    def test_logout_command_success(
        self, mock_keyring: dict[str, str | None], mocker: MockerFixture, httpx_mock: HTTPXMock
    ) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
        _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        httpx_mock.add_response(url=AuthConfig.OAUTH_REVOKE_URL, method="POST", status_code=200)

        # Act
        result = invoke("dispenser logout")

        # Assert
        assert result.exit_code == 0
        assert mock_keyring[DISPENSER_KEYRING_ID_TOKEN_KEY] is None
        assert mock_keyring[DISPENSER_KEYRING_ACCESS_TOKEN_KEY] is None
        assert mock_keyring[DISPENSER_KEYRING_REFRESH_TOKEN_KEY] is None
        assert mock_keyring[DISPENSER_KEYRING_USER_ID_KEY] is None
        verify(result.output)

    def test_logout_command_revoke_exception(
        self, mock_keyring: dict[str, str | None], mocker: MockerFixture, httpx_mock: HTTPXMock
    ) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
        _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        httpx_mock.add_exception(httpx.HTTPError("Error response"), url=AuthConfig.OAUTH_REVOKE_URL)
        clear_mock = mocker.patch("algokit.cli.dispenser.clear_dispenser_credentials")

        # Act
        result = invoke("dispenser logout")

        # Assert
        clear_mock.assert_not_called()
        assert result.exit_code == 1
        verify(result.output)


class TestLoginCommand:
    def test_login_command_already_logged_in(self, mocker: MockerFixture) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)

        # Act
        result = invoke("dispenser login")

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    def test_login_command_success_user(
        self, mock_keyring: dict[str, str | None], mocker: MockerFixture, httpx_mock: HTTPXMock
    ) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=False)
        mocker.patch("algokit.core.dispenser.jwt.decode", return_value={"sub": "user_id"})
        httpx_mock.add_response(
            url=AuthConfig.OAUTH_DEVICE_CODE_URL,
            method="POST",
            json={
                "device_code": "device_code",
                "user_code": "user_code",
                "verification_uri_complete": "https://example.com/device",
            },
        )
        httpx_mock.add_response(
            url=AuthConfig.OAUTH_TOKEN_URL,
            method="POST",
            json={
                "access_token": "access_token",
                "id_token": "id_token",
                "refresh_token": "refresh_token",
            },
        )
        mocker.patch("algokit.core.dispenser.TokenVerifier")

        # Act
        result = invoke("dispenser login")

        # Assert
        assert result.exit_code == 0
        assert mock_keyring[DISPENSER_KEYRING_ID_TOKEN_KEY] == "id_token"
        assert mock_keyring[DISPENSER_KEYRING_ACCESS_TOKEN_KEY] == "access_token"
        assert mock_keyring[DISPENSER_KEYRING_REFRESH_TOKEN_KEY] == "refresh_token"
        assert mock_keyring[DISPENSER_KEYRING_USER_ID_KEY] == "user_id"
        verify(result.output)

    @pytest.mark.parametrize(
        ("output_mode", "output_filename"),
        [
            ("stdout", None),
            ("file", "custom_file.txt"),
            ("file", None),
        ],
    )
    def test_login_command_success_ci(
        self, output_mode: str, output_filename: str | None, mocker: MockerFixture, httpx_mock: HTTPXMock, cwd: Path
    ) -> None:
        # Arrange
        httpx_mock.add_response(
            url=AuthConfig.OAUTH_DEVICE_CODE_URL,
            method="POST",
            json={
                "device_code": "device_code",
                "user_code": "user_code",
                "verification_uri_complete": "https://example.com/device",
            },
        )
        httpx_mock.add_response(
            url=AuthConfig.OAUTH_TOKEN_URL,
            method="POST",
            json={
                "access_token": "access_token",
                "id_token": "id_token",
            },
        )
        mocker.patch("algokit.core.dispenser.TokenVerifier")

        # Act
        result = invoke(
            f"dispenser login --ci -o {output_mode} {('-f ' + output_filename) if output_filename else ''}", cwd=cwd
        )

        # Assert
        assert result.exit_code == 0

        if output_mode == "file":
            expected_output_filename = output_filename if output_filename else DEFAULT_CI_TOKEN_FILENAME
            output_file_path = cwd / expected_output_filename
            assert output_file_path.exists()
            assert output_file_path.read_text() == "access_token"

        verify(result.output, options=NamerFactory.with_parameters(output_mode, output_filename))

    def test_login_command_cancelled_timeout(self, mocker: MockerFixture, httpx_mock: HTTPXMock) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=False)
        httpx_mock.add_response(
            url=AuthConfig.OAUTH_DEVICE_CODE_URL,
            method="POST",
            json={
                "device_code": "device_code",
                "user_code": "user_code",
                "verification_uri_complete": "https://example.com/device",
            },
        )
        httpx_mock.add_response(
            url=AuthConfig.OAUTH_TOKEN_URL,
            method="POST",
            json={
                "error": "authorization_pending",
                "error_description": "The user authentication is pending.",
            },
        )
        mocker.patch("algokit.core.dispenser.TokenVerifier")
        mocker.patch("algokit.core.dispenser.DISPENSER_LOGIN_TIMEOUT", 1)

        # Act
        result = invoke("dispenser login")

        # Assert
        assert result.exit_code == 1
        verify(result.output)

    @pytest.mark.parametrize(
        "refresh_successful",
        [True, False],
    )
    def test_login_command_expired_token_refresh(
        self,
        *,
        refresh_successful: bool,
        mock_keyring: dict[str, str | None],
        mocker: MockerFixture,
        httpx_mock: HTTPXMock,
    ) -> None:
        # Arrange
        _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        mocker.patch("algokit.core.dispenser._get_access_token_rsa_pub_key")
        mocker.patch("algokit.cli.dispenser.get_oauth_tokens")
        mocker.patch(
            "algokit.core.dispenser.jwt.decode",
            side_effect=[jwt.ExpiredSignatureError("Expired token"), {"sub": "new_user_id"}],
        )

        if refresh_successful:
            httpx_mock.add_response(
                url=AuthConfig.OAUTH_TOKEN_URL,
                method="POST",
                json={
                    "access_token": "access_token",
                    "id_token": "id_token",
                    "refresh_token": "refresh_token",
                },
            )
        else:
            httpx_mock.add_exception(httpx.HTTPError("Error response"), url=AuthConfig.OAUTH_TOKEN_URL)

        # Act
        result = invoke("dispenser login")

        # Assert
        assert result.exit_code == 0
        verify(result.output, options=NamerFactory.with_parameters(refresh_successful))


class TestFundCommand:
    def test_fund_command_invalid_args(
        self,
    ) -> None:
        # Act
        result = invoke("dispenser fund")

        # Assert
        assert result.exit_code == click.UsageError.exit_code
        verify(result.output)

    @pytest.mark.parametrize(
        ("with_ci_token", "use_whole_units"),
        [(True, True), (True, False), (False, True), (False, False)],
    )
    def test_fund_command_success(
        self,
        *,
        with_ci_token: bool,
        use_whole_units: bool,
        mock_keyring: dict[str, str | None],
        mocker: MockerFixture,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        if with_ci_token:
            monkeypatch.setenv("ALGOKIT_DISPENSER_ACCESS_TOKEN", "ci_access_token")
        else:
            _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
        algo_asset = DISPENSER_ASSETS[DispenserAssetName.ALGO]
        amount = 1 if use_whole_units else int(1e6)
        receiver = "A" * 58
        httpx_mock.add_response(
            url=f"{ApiConfig.BASE_URL}/fund/{algo_asset.asset_id}",
            method="POST",
            json={"amount": int(1e6), "txID": "dummy_tx_id"},
        )

        # Act
        result = invoke(f"dispenser fund -r {receiver} -a {amount} {'--whole-units' if use_whole_units else ''}")

        # Assert
        assert result.exit_code == 0
        verify(result.output, options=NamerFactory.with_parameters(with_ci_token, use_whole_units))

    def test_fund_command_http_error(
        self,
        mocker: MockerFixture,
        httpx_mock: HTTPXMock,
    ) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
        mocker.patch("algokit.core.dispenser._get_auth_token", return_value="auth_token")

        # Mock datetime.datetime.now() to always return a specific datetime
        mocker.patch("algokit.core.dispenser._get_hours_until_reset", return_value=4.0)

        algo_asset = DISPENSER_ASSETS[DispenserAssetName.ALGO]

        httpx_mock.add_exception(
            httpx.HTTPStatusError(
                "Limit exceeded",
                request=httpx.Request("POST", f"{ApiConfig.BASE_URL}/fund"),
                response=httpx.Response(
                    400,
                    request=httpx.Request("POST", f"{ApiConfig.BASE_URL}/fund"),
                    json={
                        "code": APIErrorCode.FUND_LIMIT_EXCEEDED,
                        "limit": 10_000_000,
                        "resetsAt": "2023-09-19T10:07:34.024Z",
                    },
                ),
            ),
            url=f"{ApiConfig.BASE_URL}/fund/{algo_asset.asset_id}",
            method="POST",
        )

        # Act
        result = invoke("dispenser fund -r abc -a 123")

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    def test_fund_command_not_authenticated(
        self,
        mocker: MockerFixture,
    ) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=False)

        # Act
        result = invoke("dispenser fund -r abc -a 123")

        # Assert
        assert result.exit_code == 0
        verify(result.output)


class TestRefundCommand:
    def test_refund_command_invalid_args(
        self,
    ) -> None:
        # Act
        result = invoke("dispenser refund")

        # Assert
        assert result.exit_code == click.UsageError.exit_code
        verify(result.output)

    @pytest.mark.parametrize(
        "with_ci_token",
        [True, False],
    )
    def test_refund_command_success(
        self,
        *,
        with_ci_token: bool,
        mock_keyring: dict[str, str | None],
        mocker: MockerFixture,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        if with_ci_token:
            monkeypatch.setenv("ALGOKIT_DISPENSER_ACCESS_TOKEN", "ci_access_token")
        else:
            _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
        tx_id = "some_transaction_id"
        httpx_mock.add_response(
            url=f"{ApiConfig.BASE_URL}/refund",
            method="POST",
            json={"message": f"Successfully refunded transaction {tx_id}"},
        )

        # Act
        result = invoke(f"dispenser refund -t {tx_id}")

        # Assert
        assert result.exit_code == 0
        verify(result.output, options=NamerFactory.with_parameters(with_ci_token))

    def test_refund_command_http_error(
        self,
        mock_keyring: dict[str, str | None],
        mocker: MockerFixture,
        httpx_mock: HTTPXMock,
    ) -> None:
        # Arrange
        _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
        tx_id = "some_transaction_id"
        httpx_mock.add_exception(
            httpx.HTTPError("Transaction was already processed"), url=f"{ApiConfig.BASE_URL}/refund", method="POST"
        )

        # Act
        result = invoke(f"dispenser refund -t {tx_id}")

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    def test_refund_command_not_authenticated(
        self,
        mocker: MockerFixture,
    ) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=False)
        tx_id = "some_transaction_id"

        # Act
        result = invoke(f"dispenser refund -t {tx_id}")

        # Assert
        assert result.exit_code == 0
        verify(result.output)


class TestLimitCommand:
    @pytest.mark.parametrize(
        ("with_ci_token", "use_whole_units"),
        [(True, True), (True, False), (False, True), (False, False)],
    )
    def test_limit_command_success(
        self,
        *,
        with_ci_token: bool,
        use_whole_units: bool,
        mock_keyring: dict[str, str | None],
        mocker: MockerFixture,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        if with_ci_token:
            monkeypatch.setenv("ALGOKIT_DISPENSER_ACCESS_TOKEN", "ci_access_token")
        else:
            _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
        algo_asset = DISPENSER_ASSETS[DispenserAssetName.ALGO]
        httpx_mock.add_response(
            url=f"{ApiConfig.BASE_URL}/fund/{algo_asset.asset_id}/limit",
            method="GET",
            json={"amount": 1000000},
        )

        # Act
        result = invoke(f"dispenser limit {'--whole-units' if use_whole_units else ''}")

        # Assert
        assert result.exit_code == 0
        verify(result.output, options=NamerFactory.with_parameters(with_ci_token, use_whole_units))

    def test_limit_command_http_error(
        self,
        mock_keyring: dict[str, str | None],
        mocker: MockerFixture,
        httpx_mock: HTTPXMock,
    ) -> None:
        # Arrange
        _set_mock_keyring_credentials(mock_keyring, "id_token", "access_token", "refresh_token", "user_id")
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
        algo_asset = DISPENSER_ASSETS[DispenserAssetName.ALGO]
        httpx_mock.add_exception(
            httpx.HTTPError("Unable to process limit request"),
            url=f"{ApiConfig.BASE_URL}/fund/{algo_asset.asset_id}/limit",
            method="GET",
        )

        # Act
        result = invoke("dispenser limit")

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    def test_limit_command_not_authenticated(
        self,
        mocker: MockerFixture,
    ) -> None:
        # Arrange
        mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=False)

        # Act
        result = invoke("dispenser limit")

        # Assert
        assert result.exit_code == 0
        verify(result.output)
