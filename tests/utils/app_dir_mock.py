import dataclasses
from pathlib import Path

from pytest_mock import MockerFixture


@dataclasses.dataclass
class AppDirs:
    app_config_dir: Path
    app_state_dir: Path


def tmp_app_dir(mocker: MockerFixture, tmp_path: Path) -> AppDirs:
    app_config_dir = tmp_path / "config"
    app_config_dir.mkdir()
    mocker.patch("rdmak.core.sandbox.get_app_config_dir").return_value = app_config_dir

    app_state_dir = tmp_path / "state"
    app_state_dir.mkdir()
    # mocker.patch("algokit.cli.{feature}.get_app_state_dir").return_value = app_state_dir

    return AppDirs(app_config_dir=app_config_dir, app_state_dir=app_state_dir)
