from unittest.mock import Mock

import pytest
from algokit.core import sandbox
from algokit.core.sandbox import ALGOD_HEALTH_URL
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests.utils.proc_mock import ProcMock


@pytest.fixture(autouse=True)
def algod_health_fast_timings(mocker: MockerFixture) -> None:  # noqa: ignore[PT004]
    mocker.patch("algokit.core.sandbox.DEFAULT_WAIT_FOR_ALGOD", 0.1)
    mocker.patch("algokit.core.sandbox.DEFAULT_HEALTH_TIMEOUT", 0.1)


@pytest.fixture()
def health_success(httpx_mock: HTTPXMock) -> None:  # noqa: ignore[PT004]
    httpx_mock.add_response(url=ALGOD_HEALTH_URL)


@pytest.fixture()
def localnet_up_to_date(proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    proc_mock.set_output(
        ["docker", "image", "inspect", "algorand/algod:latest", "--format", "{{.RepoDigests}}"],
        ["[algorand/algod@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa]"],
    )

    proc_mock.set_output(
        ["docker", "image", "inspect", "makerxau/algorand-indexer-dev:latest", "--format", "{{.RepoDigests}}"],
        ["[makerxau/algorand-indexer-dev@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb]"],
    )

    httpx_mock.add_response(
        url="https://registry.hub.docker.com/v2/repositories/makerxau/algorand-indexer-dev/tags/latest",
        json={
            "digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        },
    )

    httpx_mock.add_response(
        url="https://registry.hub.docker.com/v2/repositories/algorand/algod/tags/latest",
        json={
            "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        },
    )


@pytest.fixture()
def localnet_out_date(proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    proc_mock.set_output(
        ["docker", "image", "inspect", "algorand/algod:latest", "--format", "{{.RepoDigests}}"],
        ["[algorand/algod@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb]"],
    )

    proc_mock.set_output(
        ["docker", "image", "inspect", "makerxau/algorand-indexer-dev:latest", "--format", "{{.RepoDigests}}"],
        ["[makerxau/algorand-indexer-dev@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa]"],
    )

    httpx_mock.add_response(
        url="https://registry.hub.docker.com/v2/repositories/makerxau/algorand-indexer-dev/tags/latest",
        json={
            "digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        },
    )

    httpx_mock.add_response(
        url="https://registry.hub.docker.com/v2/repositories/algorand/algod/tags/latest",
        json={
            "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        },
    )
