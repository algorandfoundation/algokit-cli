from unittest.mock import Mock
import httpx

import pytest
from algokit.core import sandbox
from algokit.core.sandbox import ALGOD_HEALTH_URL
from pytest_httpx import HTTPXMock, httpx_mock
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
def sandbox_mock() -> None:  # noqa: PT004
    sandbox.ComposeSandbox.check_docker_compose_for_new_image_versions = Mock()


@pytest.fixture()
def docker_cmd_mock(mocker: MockerFixture) -> ProcMock:
    image_name = "makerxau/algorand-indexer-dev:latest"

    # args = image_name.split(":")
    # name = args[0]
    # tag = args[1] if len(args) > 1 else "latest"
    # url = f"https://registry.hub.docker.com/v2/repositories/{name}/tags/{tag}"

    # httpx_mock.add_response(
    #     url=url,
    #     json={
    #         "creator": 15752087,
    #         "id": 374471196,
    #         "last_updated": "2023-06-26T14:12:05.720589Z",
    #         "last_updater": 15752087,
    #         "last_updater_username": "algoservice",
    #         "name": "latest",
    #         "repository": 16857316,
    #         "full_size": 197616288,
    #         "v2": True,
    #         "tag_status": "active",
    #         "tag_last_pulled": "2023-08-07T06:12:23.743761Z",
    #         "tag_last_pushed": "2023-06-26T14:12:05.720589Z",
    #         "media_type": "application/vnd.docker.distribution.manifest.list.v2+json",
    #         "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    #     },
    # )

    proc_mock = ProcMock()
    # add a default for docker compose version
    arg = "{{.RepoDigests}}"

    proc_mock.set_output(
        ["docker", "image", "inspect", image_name, "--format", arg],
        ["algorand/algod@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
    )
    mocker.patch("algokit.core.proc.Popen").side_effect = proc_mock.popen
    return proc_mock
