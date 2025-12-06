import json
import time

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from algokit.core.sandbox import (
    ALGORAND_IMAGE,
    IMAGE_VERSION_CHECK_INTERVAL,
    INDEXER_IMAGE,
    ComposeSandbox,
    _get_image_version_cache_path,
    _update_image_version_cache,
    get_algod_network_template,
    get_conduit_yaml,
    get_config_json,
    get_docker_compose_yml,
    get_proxy_config,
)
from tests.utils.approvals import verify
from tests.utils.proc_mock import ProcMock


def test_get_config_json() -> None:
    config_json = json.loads(get_config_json())
    verify(json.dumps(config_json, indent=2))


def test_get_conduit_yaml() -> None:
    conduit_yaml = get_conduit_yaml()
    verify(conduit_yaml)


def test_get_docker_compose_yml() -> None:
    docker_compose_yml = get_docker_compose_yml()
    verify(docker_compose_yml)


def test_algod_network_template_json() -> None:
    algod_network_template_json = get_algod_network_template()
    verify(algod_network_template_json)


def test_proxy_config() -> None:
    proxy_config = get_proxy_config()
    verify(proxy_config)


@pytest.fixture
def _mock_image_check_responses(proc_mock: ProcMock, httpx_mock: HTTPXMock) -> None:
    """Mock the docker and HTTP responses needed for image version checks."""
    arg = "{{range .RepoDigests}}{{println .}}{{end}}"
    proc_mock.set_output(
        ["docker", "image", "inspect", ALGORAND_IMAGE, "--format", arg],
        ["tag@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"],
    )
    proc_mock.set_output(
        ["docker", "image", "inspect", INDEXER_IMAGE, "--format", arg],
        ["tag@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"],
    )
    httpx_mock.add_response(
        url="https://registry.hub.docker.com/v2/repositories/algorand/indexer/tags/latest",
        json={"digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
    )
    httpx_mock.add_response(
        url="https://registry.hub.docker.com/v2/repositories/algorand/algod/tags/latest",
        json={"digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )


@pytest.mark.use_real_image_version_cache
@pytest.mark.usefixtures("app_dir_mock", "_mock_image_check_responses")
def test_check_docker_compose_for_new_image_versions_no_cache(proc_mock: ProcMock) -> None:
    """Should check versions when cache file doesn't exist."""
    cache_path = _get_image_version_cache_path()
    if cache_path.exists():
        cache_path.unlink()

    sandbox = ComposeSandbox()
    sandbox.check_docker_compose_for_new_image_versions()

    assert cache_path.exists()
    # Verify check was run
    assert any("image" in call.command and "inspect" in call.command for call in proc_mock.called)


@pytest.mark.use_real_image_version_cache
@pytest.mark.usefixtures("app_dir_mock")
def test_check_docker_compose_for_new_image_versions_cache_fresh(proc_mock: ProcMock) -> None:
    """Should skip check when cache is fresh."""
    _update_image_version_cache()

    sandbox = ComposeSandbox()
    sandbox.check_docker_compose_for_new_image_versions()

    # Verify check was skipped
    assert not any("image" in call.command and "inspect" in call.command for call in proc_mock.called)


@pytest.mark.use_real_image_version_cache
@pytest.mark.usefixtures("app_dir_mock", "_mock_image_check_responses")
def test_check_docker_compose_for_new_image_versions_cache_expired(proc_mock: ProcMock, mocker: MockerFixture) -> None:
    """Should check versions when cache is expired."""
    _update_image_version_cache()
    # Mock time to be past the cache interval
    mocker.patch("algokit.core.sandbox.time.time", return_value=time.time() + IMAGE_VERSION_CHECK_INTERVAL + 1)

    sandbox = ComposeSandbox()
    sandbox.check_docker_compose_for_new_image_versions()

    # Verify check was run
    assert any("image" in call.command and "inspect" in call.command for call in proc_mock.called)
