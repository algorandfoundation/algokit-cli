import algokit_algosdk.account
from pytest_httpx import HTTPXMock

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def test_nfd_lookup_by_domain_success(httpx_mock: HTTPXMock) -> None:
    # Arrange
    httpx_mock.add_response(
        url="https://api.nf.domains/nfd/dummy.algo?view=brief&poll=false",
        json={
            "name": "dummy.algo",
            "owner": "A" * 58,
            "depositAccount": "A" * 58,
            "properties": {},
        },
    )

    # Act
    result = invoke("task nfd-lookup dummy.algo")

    # Assert
    assert result.exit_code == 0
    verify(result.output)


def test_nfd_lookup_by_address_success(httpx_mock: HTTPXMock) -> None:
    # Arrange
    _, dummy_wallet = algokit_algosdk.account.generate_account()  # type: ignore[no-untyped-call]
    httpx_mock.add_response(
        url=f"https://api.nf.domains/nfd/lookup?address={dummy_wallet}&view=thumbnail&allowUnverified=false",
        json={
            dummy_wallet: {
                "appID": 222222222,
                "state": "owned",
                "timeChanged": "2022-02-02",
                "depositAccount": "A" * 58,
                "name": "dummy.algo",
                "owner": "A" * 58,
                "properties": {},
                "caAlgo": ["A" * 58],
            }
        },
    )

    # Act
    result = invoke(f"task nfd-lookup {dummy_wallet}")

    # Assert
    assert result.exit_code == 0
    verify(result.output.replace(dummy_wallet, "A" * 58))


def test_nfd_lookup_error(httpx_mock: HTTPXMock) -> None:
    # Arrange
    httpx_mock.add_response(
        url="https://api.nf.domains/nfd/dummy.algo?view=brief&poll=false",
        status_code=400,
        json={"message": "Invalid request"},
    )

    # Act
    result = invoke("task nfd-lookup dummy.algo")

    # Assert
    assert result.exit_code == 1
    assert "Invalid request" in result.output


def test_nfd_lookup_invalid_input() -> None:
    # Act
    result = invoke("task nfd-lookup dummy")

    # Assert
    assert result.exit_code == 1
    assert "Invalid input. Must be either a valid NFD domain or an Algorand address." in result.output
