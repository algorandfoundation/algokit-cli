import logging
import re
import shutil
from pathlib import Path, PurePath

from algokit.core.conf import get_app_config_dir

logger = logging.getLogger(__name__)


def get_volume_mount_path_docker() -> Path:
    return Path("/root/goal_mount/")


def get_volume_mount_path_local() -> Path:
    return get_app_config_dir().joinpath("sandbox", "goal_mount")


def is_path_or_filename(argument: str) -> bool:
    filename_pattern = re.compile(r"^[\w-]+\.\w+$")
    return filename_pattern.match(argument) is not None or len(PurePath(argument).parts) > 1


def delete_files_from_volume_mount(filename: str, volume_mount_path_docker: Path) -> None:
    try:
        volume_mount_path_docker.joinpath(filename).unlink()
    except Exception as e:
        logger.error(e)


def list_files_in_volume(volume_path: Path) -> list[str]:
    file_paths = []
    if volume_path.exists() and volume_path.is_dir():
        for file in volume_path.rglob("*"):
            if file.is_file():
                file_paths.append(str(file))
    else:
        logger.error(f"{volume_path} does not exist or is not a directory.")
    return file_paths


def preprocess_command_args(
    command: list[str], volume_mount_path_local: Path, docker_mount_path_local: Path
) -> tuple[list[str], list[Path], list[str]]:
    input_filenames = []
    output_filenames = []
    try:
        for i, arg in enumerate(command):
            if is_path_or_filename(arg):
                arg_path = Path(arg)
                arg_changed = docker_mount_path_local.joinpath(arg_path.name)
                command[i] = str(arg_changed)

                file_exists = arg_path.exists() or Path.cwd().joinpath(arg_path.name).exists()
                is_output_arg = i > 0 and command[i - 1] in ["-o", "--outdir", "--outfile"]
                if file_exists and not is_output_arg:
                    input_filenames.append(arg_path.name)
                    shutil.copy(arg_path, volume_mount_path_local)
                elif is_output_arg:  # it is an output file that is not exist now
                    output_filenames.append(arg_path)
                else:
                    raise FileNotFoundError(f"{arg} does not exist.")
    except Exception as e:
        logger.error(e)
        raise e
    return input_filenames, output_filenames, command


def post_process(input_filenames: list, output_filenames: list[Path], volume_mount_path_local: Path) -> None:
    for input_filename in input_filenames:
        delete_files_from_volume_mount(input_filename, volume_mount_path_local)

    files_in_volume_mount = {Path(file).name for file in list_files_in_volume(volume_mount_path_local)}
    for output_filename in output_filenames:
        if output_filename.name in files_in_volume_mount:
            target_path = (
                output_filename if output_filename.is_absolute() else Path.cwd().joinpath(output_filename.name)
            )
            shutil.copy(volume_mount_path_local.joinpath(output_filename.name), target_path)
            delete_files_from_volume_mount(output_filename.name, volume_mount_path_local)
