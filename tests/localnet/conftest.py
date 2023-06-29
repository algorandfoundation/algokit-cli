import pytest
from algokit.core.constants import ALGOD_HEALTH_URL
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def algod_health_fast_timings(mocker: MockerFixture) -> None:  # noqa: ignore[PT004]
    mocker.patch("algokit.core.sandbox.DEFAULT_WAIT_FOR_ALGOD", 0.1)
    mocker.patch("algokit.core.sandbox.DEFAULT_HEALTH_TIMEOUT", 0.1)


@pytest.fixture()
def health_success(httpx_mock: HTTPXMock) -> None:  # noqa: ignore[PT004]
    httpx_mock.add_response(url=ALGOD_HEALTH_URL)
