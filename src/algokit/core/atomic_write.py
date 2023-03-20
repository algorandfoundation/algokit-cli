import contextlib
import os
import shutil
import stat
from pathlib import Path
from typing import Literal


def atomic_write(file_contents: str, target_file_path: Path, mode: Literal["a", "w"] = "w") -> None:
    # if target path is a symlink, we want to use the real path as the replacement target,
    # otherwise we'd just be overwriting the symlink
    target_file_path = target_file_path.resolve()
    temp_file_path = target_file_path.with_suffix(f"{target_file_path.suffix}.algokit~")
    try:
        # preserve file metadata if it already exists
        with contextlib.suppress(FileNotFoundError):
            _copy_with_metadata(target_file_path, temp_file_path)
        # write content to new temp file
        with temp_file_path.open(mode=mode, encoding="utf-8") as fp:
            fp.write(file_contents)
        # overwrite destination with the temp file
        temp_file_path.replace(target_file_path)
    finally:
        temp_file_path.unlink(missing_ok=True)


def _copy_with_metadata(source: Path, target: Path) -> None:
    # copy content, stat-info (mode too), timestamps...
    shutil.copy2(source, target)
    # try copy owner+group if platform supports it
    if hasattr(os, "chown"):
        # copy owner and group
        st = source.stat()
        os.chown(target, st[stat.ST_UID], st[stat.ST_GID])
