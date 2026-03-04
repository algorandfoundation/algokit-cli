import logging
import os
import stat
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_mock import MockerFixture

from algokit.cli import _check_binary_deprecation
from algokit.core.utils import find_all_on_path

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def _make_executable(path: Path) -> None:
    path.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_find_all_on_path_returns_matches_in_path_order(tmp_path: Path, monkeypatch: "MonkeyPatch") -> None:
    legacy_dir = tmp_path / "legacy-bin"
    uv_dir = tmp_path / "uv-bin"
    legacy_dir.mkdir()
    uv_dir.mkdir()

    legacy_algokit = legacy_dir / "algokit"
    uv_algokit = uv_dir / "algokit"
    _make_executable(legacy_algokit)
    _make_executable(uv_algokit)

    monkeypatch.setenv("PATH", f"{legacy_dir}{os.pathsep}{uv_dir}")

    paths = find_all_on_path("algokit")

    assert [path.resolve() for path in paths] == [legacy_algokit.resolve(), uv_algokit.resolve()]


def test_find_all_on_path_deduplicates_repeated_entries(tmp_path: Path, monkeypatch: "MonkeyPatch") -> None:
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    algokit = tools_dir / "algokit"
    _make_executable(algokit)

    monkeypatch.setenv("PATH", f"{tools_dir}{os.pathsep}{tools_dir}")

    paths = find_all_on_path("algokit")

    assert [path.resolve() for path in paths] == [algokit.resolve()]


def test_check_binary_deprecation_warns_when_multiple_algokit_are_on_path(
    caplog: "LogCaptureFixture", mocker: MockerFixture, monkeypatch: "MonkeyPatch"
) -> None:
    mocker.patch("algokit.cli.is_binary_mode", return_value=True)
    mocker.patch(
        "algokit.cli.find_all_on_path",
        return_value=[Path("/usr/local/bin/algokit"), Path("/home/user/.local/bin/algokit")],
    )
    monkeypatch.setattr(sys, "executable", "/usr/local/bin/algokit")

    with caplog.at_level(logging.WARNING):
        _check_binary_deprecation()

    assert "Multiple `algokit` executables were found on PATH." in caplog.text
    assert "/usr/local/bin/algokit" in caplog.text
    assert "/home/user/.local/bin/algokit" in caplog.text
