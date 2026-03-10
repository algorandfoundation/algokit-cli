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


def _make_executable(path: Path) -> Path:
    executable_path = path.with_suffix(".exe") if os.name == "nt" else path
    executable_path.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    executable_path.chmod(executable_path.stat().st_mode | stat.S_IXUSR)
    return executable_path


def test_find_all_on_path_returns_matches_in_path_order(tmp_path: Path, monkeypatch: "MonkeyPatch") -> None:
    legacy_dir = tmp_path / "legacy-bin"
    uv_dir = tmp_path / "uv-bin"
    legacy_dir.mkdir()
    uv_dir.mkdir()

    legacy_algokit = _make_executable(legacy_dir / "algokit")
    uv_algokit = _make_executable(uv_dir / "algokit")

    monkeypatch.setenv("PATH", f"{legacy_dir}{os.pathsep}{uv_dir}")

    paths = find_all_on_path("algokit")

    assert [path.resolve() for path in paths] == [legacy_algokit.resolve(), uv_algokit.resolve()]


def test_find_all_on_path_deduplicates_repeated_entries(tmp_path: Path, monkeypatch: "MonkeyPatch") -> None:
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    algokit = _make_executable(tools_dir / "algokit")

    monkeypatch.setenv("PATH", f"{tools_dir}{os.pathsep}{tools_dir}")

    paths = find_all_on_path("algokit")

    assert [path.resolve() for path in paths] == [algokit.resolve()]


def test_check_binary_deprecation_warns_when_multiple_algokit_are_on_path(
    caplog: "LogCaptureFixture", mocker: MockerFixture, monkeypatch: "MonkeyPatch"
) -> None:
    mocker.patch("algokit.cli.is_binary_mode", return_value=True)
    first_algokit_path = Path("/usr/local/bin/algokit")
    second_algokit_path = Path("/home/user/.local/bin/algokit")
    mocker.patch("algokit.cli.find_all_on_path", return_value=[first_algokit_path, second_algokit_path])
    monkeypatch.setattr(sys, "executable", str(first_algokit_path))

    with caplog.at_level(logging.WARNING):
        _check_binary_deprecation()

    assert "Multiple `algokit` executables were found on PATH." in caplog.text
    assert str(first_algokit_path) in caplog.text
    assert str(second_algokit_path) in caplog.text
