import logging
import re
import shutil
from pathlib import Path, PurePath

from algokit.core.conf import get_app_config_dir
from algokit.core.config_commands.container_engine import get_container_engine
from algokit.core.sandbox import ContainerEngine

logger = logging.getLogger(__name__)


def get_volume_mount_path_docker() -> Path:
    return Path("/root/goal_mount/")


def get_volume_mount_path_local(directory_name: str) -> Path:
    path = get_app_config_dir().joinpath(directory_name, "goal_mount")
    if get_container_engine() == ContainerEngine.PODMAN:
        # Pre create the directory to avoid permission issues
        path.mkdir(parents=True, exist_ok=True)
    return path


filename_pattern = re.compile(r"^[\w\-\.]+\.\w+$")


def is_path_or_filename(argument: str) -> bool:
    path = PurePath(argument)
    return len(path.parts) > 1 or (len(path.parts) == 1 and filename_pattern.match(path.parts[0]) is not None)


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
) -> tuple[list[Path], list[Path], list[str]]:
    input_files = []
    output_files = []
    try:
        for i, arg in enumerate(command):
            if is_path_or_filename(arg):
                absolute_arg_path = Path(arg).expanduser().absolute()
                arg_changed = docker_mount_path_local.joinpath(absolute_arg_path.name)
                command[i] = str(arg_changed)

                file_exists = absolute_arg_path.exists()
                is_output_arg = i > 0 and command[i - 1] in [
                    "-o",
                    "--outdir",
                    "--outfile",
                    "--out",
                    "--result-out",
                    "--lsig-out",
                ]
                if file_exists and not is_output_arg:
                    input_files.append(absolute_arg_path)
                    shutil.copy(absolute_arg_path, volume_mount_path_local)
                elif is_output_arg:  # it is an output file that doesn't exist yet
                    output_files.append(absolute_arg_path)
                else:
                    raise FileNotFoundError(f"{arg} does not exist.")
    except Exception as e:
        logger.error(e)
        raise e
    return input_files, output_files, command


def post_process(input_files: list[Path], output_files: list[Path], volume_mount_path_local: Path) -> None:
    for input_file in input_files:
        delete_files_from_volume_mount(input_file.name, volume_mount_path_local)

    files_in_volume_mount = {Path(file) for file in list_files_in_volume(volume_mount_path_local)}
    for output_file in output_files:
        stem = output_file.stem
        ext = output_file.suffix

        # Copy outputs split into multiple files. For example `goal clerk split -i ./input.gtxn -o ./output.txn`
        # will produce a file (output-0.txn etc) for each transaction in the group being split.
        r = re.compile(rf"^(?:{stem})(?:-[0-9]+)?(?:\{ext})$") if ext else re.compile(rf"^(?:{stem})(?:-[0-9]+)?$")

        matched_files_in_volume_mount = filter(lambda f: (r.match(f.name)), files_in_volume_mount)

        for matched_file_in_volume_mount in matched_files_in_volume_mount:
            shutil.copy(
                volume_mount_path_local.joinpath(matched_file_in_volume_mount.name),
                output_file.parent.joinpath(matched_file_in_volume_mount.name),
            )
            delete_files_from_volume_mount(matched_file_in_volume_mount.name, volume_mount_path_local)
