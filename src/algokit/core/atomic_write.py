import os
import platform
import shutil
import stat
import tempfile
from pathlib import Path


# from https://python.plainenglish.io/simple-safe-atomic-writes-in-python3-44b98830a013
def atomic_write(file_contents: list[str], target_file_path: Path, mode: str = "w") -> None:
    # Use the same directory as the destination file so replace is atomic
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=target_file_path.parent)
    temp_file_path = Path(temp_file.name)
    temp_file.close()
    try:
        # preserve file metadata if it already exists
        if target_file_path.exists():
            _copy_with_metadata(target_file_path, temp_file_path)
        with open(temp_file_path, mode) as file:
            file.writelines(file_contents)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_file_path, target_file_path)
    finally:
        temp_file_path.unlink(missing_ok=True)


def _copy_with_metadata(source: Path, target: Path) -> None:
    # copy content, stat-info (mode too), timestamps...
    shutil.copy2(source, target)
    os_type = platform.system().lower()
    if os_type != "windows":
        # copy owner and group
        st = os.stat(source)
        os.chown(target, st[stat.ST_UID], st[stat.ST_GID])
