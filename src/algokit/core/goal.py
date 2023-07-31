import logging
import shutil
from pathlib import Path, PurePath

from algokit.core.conf import get_app_config_dir

logger = logging.getLogger(__name__)


def get_volume_mount_path_docker() -> Path:
    return Path("/root/goal_mount/")


def get_volume_mount_path_local() -> Path:
    return Path(f"{get_app_config_dir()}/goal_mount/")


def make_absolute_path(arg: Path) -> Path:
    if arg.is_absolute():
        return arg
    else:
        return Path.cwd().joinpath(arg)


def local_fs_to_docker_fs(arg: Path, volume_mount_path_docker: Path) -> Path:
    return volume_mount_path_docker.joinpath(arg.name)


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
) -> tuple[list, list[Path], list[str]]:
    copied_filenames = []
    output_filenames = []
    # TODO: double check for the root cause for the behaviour of the bind
    # It takes N seconds for file to appear on your local filesystem, if the solution is type volume
    # lets use that instead of bind otherwise we need polling
    # And make sure command path is modified to the paths relative to docker container fs
    try:
        for i, arg in enumerate(command):
            if len(PurePath(arg).parts) > 1:  # it is a path
                arg_path = Path(arg)
                if make_absolute_path(arg_path).exists():  # it is an input file
                    shutil.copy(make_absolute_path(arg_path), volume_mount_path_local)
                    arg_changed = docker_mount_path_local.joinpath(arg_path.name)
                    copied_filenames.append(arg_changed.name)
                    command[i] = str(arg_changed)
                else:  # it is an output file that is not exist now
                    output_filenames.append(arg_path)
                    # TODO: make sure you replace the local path with the docker path
    except Exception as e:
        logger.error(e)
    return copied_filenames, output_filenames, command


def post_process(copied_filenames: list, output_filenames: list[Path], volume_mount_path_local: Path) -> None:
    for copied_filename in copied_filenames:
        delete_files_from_volume_mount(copied_filename, volume_mount_path_local)

    volume_mount_files = list_files_in_volume(volume_mount_path_local)
    output_filenames_set = set(output_filenames)
    for volume_mount_file in volume_mount_files:
        volume_file_name = Path(volume_mount_file).name
        if volume_file_name in output_filenames_set:
            shutil.copy(volume_mount_path_local.joinpath(volume_file_name), Path.cwd().joinpath(volume_file_name))
            # TODO: make sure outputs and inputs are all parsed to absolute paths
