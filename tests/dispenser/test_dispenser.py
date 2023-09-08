import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


@pytest.fixture(autouse=True)
def _mock_keyring(mocker: MockerFixture) -> None:
    mocker.patch("keyring.set_password")
    mocker.patch("keyring.get_password")
    mocker.patch("keyring.delete_password")
    mocker.patch("jwt.decode")


@pytest.mark.parametrize(
    "command",
    ["logout", "login", "refund", "fund", "limit"],
)
def test_no_internet_access(command: str, mocker: MockerFixture) -> None:
    is_network_available_mock = mocker.patch("algokit.cli.dispenser.is_network_available", return_value=False)

    result = invoke(f"dispenser {command}")

    is_network_available_mock.assert_called()
    assert result.exit_code == 1
    assert result.output == "ERROR: Please connect to internet first\n"


def test_logout_command_already_logged_out(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=False)
    result = invoke("dispenser logout")

    assert result.exit_code == 0
    verify(result.output)


def test_logout_command_success(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
    mocker.patch("algokit.cli.dispenser.revoke_refresh_token")
    mocker.patch("algokit.core.dispenser.keyring")
    result = invoke("dispenser logout")

    assert result.exit_code == 0
    verify(result.output)


def test_logout_command_revoke_exception(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
    mocker.patch("algokit.cli.dispenser.revoke_refresh_token", side_effect=Exception("Failed to revoke token"))
    clear_mock = mocker.patch("algokit.cli.dispenser.clear_dispenser_credentials")

    result = invoke("dispenser logout")

    clear_mock.assert_not_called()

    assert result.exit_code == 1
    verify(result.output)


# Login command tests


def test_login_command_already_logged_in(mocker: MockerFixture) -> None:
    mocker.patch("algokit.cli.dispenser.is_authenticated", return_value=True)
    result = invoke("dispenser login")

    assert result.exit_code == 0
    verify(result.output)


def test_login_command_success(mocker: MockerFixture, httpx_mock: HTTPXMock) -> None:
    # Mock the response for the device code request in get_oauth_tokens
    httpx_mock.add_response(
        url="https://dispenser-staging.eu.auth0.com/oauth/device/code",
        method="POST",
        json={
            "device_code": "device_code",
            "user_code": "user_code",
            "verification_uri_complete": "https://example.com/device",
        },
    )

    # Mock the response for the token request in get_oauth_tokens
    httpx_mock.add_response(
        url="https://dispenser-staging.eu.auth0.com/oauth/token",
        method="POST",
        json={
            "access_token": "access_token",
            "id_token": "id_token",
            "refresh_token": "refresh_token",
        },
    )

    # Mock the _validate_jwt_id_token function to avoid token validation
    mocker.patch("algokit.core.dispenser._validate_jwt_id_token")

    result = invoke("dispenser login")

    assert result.exit_code == 0
    verify(result.output)
