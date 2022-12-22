from unittest.mock import MagicMock

import pytest
from approvaltests.scrubbers.scrubbers import Scrubber, combine_scrubbers
from pytest_mock import MockerFixture
from utils.app_dir_mock import AppDirs
from utils.approvals import normalize_path, verify
from utils.click_invoker import invoke

CURRENT_VERSION = "0.1.0"
NEW_VERSION = "999.99.99"


class MockReleaseResponse:
    def __init__(self, tag_name: str, status_code: int = 200):
        self.tag_name = tag_name
        self.status_code = status_code

    def json(self) -> dict:
        return {"tag_name": self.tag_name}


def make_scrubber(app_dir_mock: AppDirs) -> Scrubber:
    return combine_scrubbers(
        lambda x: normalize_path(x, str(app_dir_mock.app_config_dir), "{app_config}"),
        lambda x: normalize_path(x, str(app_dir_mock.app_state_dir), "{app_state}"),
        lambda x: x.replace(CURRENT_VERSION, "{current_version}"),
        lambda x: x.replace(NEW_VERSION, "{new_version}"),
    )


@pytest.fixture(autouse=True)
def setup(latest_version_mock: MagicMock, mocker: MockerFixture, app_dir_mock: AppDirs) -> None:
    # restore latest version behaviour
    mocker.stop(latest_version_mock)

    mocker.patch("requests.get").return_value = MockReleaseResponse(f"v{NEW_VERSION}")
    mocker.patch("algokit.core.version_check.get_app_config_dir").return_value = app_dir_mock.app_config_dir
    mocker.patch("algokit.core.version_check.get_app_state_dir").return_value = app_dir_mock.app_state_dir
    # make bootstrap env a no-op
    mocker.patch("algokit.cli.bootstrap.bootstrap_env")


def test_version_check_queries_github_when_no_cache(app_dir_mock: AppDirs):
    # bootstrap env is a nice simple command we can use to test the version check side effects
    result = invoke("bootstrap env")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_uses_cache(app_dir_mock: AppDirs):
    version_cache = app_dir_mock.app_state_dir / "last-version-check"
    version_cache.write_text("999.99.99", encoding="utf-8")
    result = invoke("bootstrap env")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_respects_disable_config(app_dir_mock: AppDirs):
    (app_dir_mock.app_config_dir / "disable-version-check").touch()
    result = invoke("bootstrap env")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_respects_skip_option(app_dir_mock: AppDirs):
    result = invoke("--skip-version-check bootstrap env")

    assert result.exit_code == 0
    verify(result.output, scrubber=make_scrubber(app_dir_mock))


def test_version_check_disable_version_check(app_dir_mock: AppDirs):
    disable_version_check_path = app_dir_mock.app_config_dir / "disable-version-check"
    result = invoke("--disable-version-check")

    assert result.exit_code == 0
    assert disable_version_check_path.exists()
    verify(result.output, scrubber=make_scrubber(app_dir_mock))
