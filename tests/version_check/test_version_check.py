import os
from importlib import metadata
from time import time

import pytest
from algokit.core.conf import PACKAGE_NAME
from algokit.core.version_prompt import LATEST_URL, VERSION_CHECK_INTERVAL
from approvaltests.scrubbers.scrubbers import Scrubber, combine_scrubbers
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from tests.utils.app_dir_mock import AppDirs
from tests.utils.approvals import normalize_path, verify
from tests.utils.click_invoker import invoke

CURRENT_VERSION = metadata.version(PACKAGE_NAME)
NEW_VERSION = "999.99.99"


def make_scrubber(app_dir_mock: AppDirs) -> Scrubber:
    return combine_scrubbers(
        lambda x: normalize_path(x, str(app_dir_mock.app_config_dir), "{app_config}"),
        lambda x: normalize_path(x, str(app_dir_mock.app_state_dir), "{app_state}"),
        lambda x: x.replace(CURRENT_VERSION, "{current_version}"),
        lambda x: x.replace(NEW_VERSION, "{new_version}"),
    )


@pytest.fixture(autouse=True)
def _setup(mocker: MockerFixture, app_dir_mock: AppDirs) -> None:
    mocker.patch("algokit.core.version_prompt.get_app_config_dir").return_value = app_dir_mock.app_config_dir
    mocker.patch("algokit.core.version_prompt.get_app_state_dir").return_value = app_dir_mock.app_state_dir
    # make bootstrap env a no-op
    mocker.patch("algokit.cli.bootstrap.bootstrap_env")


def test_version_check_queries_github_when_no_cache(app_dir_mock: AppDirs, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=LATEST_URL, json={"tag_name": f"v{NEW_VERSION}"})

    # bootstrap env is a nice simple command we can use to test the version check side effects
    result = invoke("bootstrap env", skip_version_check=False)

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


@pytest.mark.parametrize(
    ("current_version", "latest_version", "warning_expected"),
    [
        ("0.2.0", "0.3.0", True),
        ("0.25.0", "0.30.0", True),
        ("0.3.0", "0.29.0", True),
        ("999.99.99", "1000.00.00", True),
        ("999.99.99-beta", "1000.00.00", True),
        ("999.99.99-alpha", "999.99.99-beta", True),
        ("0.25.0", "1.0.0", True),
        ("0.29.0", "1.0.0", True),
        ("0.3.0", "1.0.0", True),
        ("0.3.0", "0.2.0", False),
        ("0.3.0", "0.3.0", False),
        ("0.30.0", "0.25.0", False),
        ("0.29.0", "0.3.0", False),
        ("0.30.0", "0.30.0", False),
        ("1.0.0", "0.25.0", False),
        ("1.0.0", "0.29.0", False),
        ("1.0.0", "0.3.0", False),
        ("1.0.0", "1.0.0", False),
        ("999.99.99", "998.0.0", False),
        ("999.99.99", "999.99.0", False),
        ("999.99.99", "999.99.99", False),
        ("999.99.99-beta", "998.99.99", False),
        ("999.99.99-beta", "999.99.99-alpha", False),
    ],
)
def test_version_check_only_warns_if_newer_version_is_found(
    app_dir_mock: AppDirs, mocker: MockerFixture, current_version: str, latest_version: str, *, warning_expected: bool
) -> None:
    mocker.patch("algokit.core.version_prompt.get_current_package_version").return_value = current_version
    version_cache = app_dir_mock.app_state_dir / "last-version-check"
    version_cache.write_text(latest_version, encoding="utf-8")
    result = invoke("bootstrap env", skip_version_check=False)

    if warning_expected:
        assert f"version {latest_version} is available" in result.output
    else:
        assert f"version {latest_version} is available" not in result.output


def test_version_check_uses_cache(app_dir_mock: AppDirs) -> None:
    version_cache = app_dir_mock.app_state_dir / "last-version-check"
    version_cache.write_text("1234.56.78", encoding="utf-8")
    result = invoke("bootstrap env", skip_version_check=False)

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_queries_github_when_cache_out_of_date(app_dir_mock: AppDirs, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=LATEST_URL, json={"tag_name": f"v{NEW_VERSION}"})
    version_cache = app_dir_mock.app_state_dir / "last-version-check"
    version_cache.write_text("1234.56.78", encoding="utf-8")
    modified_time = time() - VERSION_CHECK_INTERVAL - 1
    os.utime(version_cache, (modified_time, modified_time))

    result = invoke("bootstrap env", skip_version_check=False)

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_respects_disable_config(app_dir_mock: AppDirs) -> None:
    (app_dir_mock.app_config_dir / "disable-version-prompt").touch()
    result = invoke("bootstrap env", skip_version_check=False)

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_respects_skip_option(app_dir_mock: AppDirs) -> None:
    result = invoke("--skip-version-check bootstrap env", skip_version_check=False)

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_disable_version_check(app_dir_mock: AppDirs) -> None:
    disable_version_check_path = app_dir_mock.app_config_dir / "disable-version-prompt"
    result = invoke("config version-prompt disable")

    assert result.exit_code == 0
    assert disable_version_check_path.exists()
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_enable_version_check(app_dir_mock: AppDirs) -> None:
    disable_version_check_path = app_dir_mock.app_config_dir / "disable-version-prompt"
    disable_version_check_path.touch()
    result = invoke("config version-prompt enable")

    assert result.exit_code == 0
    assert not disable_version_check_path.exists()
    verify(result.output, scrubber=make_scrubber(app_dir_mock))
