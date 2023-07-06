import contextlib
import os
import re
import typing as t


def extract_version_triple(version_str: str) -> str:
    match = re.search(r"\d+\.\d+\.\d+", version_str)
    if not match:
        raise ValueError("Unable to parse version number")
    return match.group()


def is_minimum_version(system_version: str, minimum_version: str) -> bool:
    system_version_as_tuple = tuple(map(int, system_version.split(".")))
    minimum_version_as_tuple = tuple(map(int, minimum_version.split(".")))
    return system_version_as_tuple >= minimum_version_as_tuple


@contextlib.contextmanager
def isolate_environ_changes() -> t.Iterator[None]:
    """Undo any changes to os.environ on scope exit"""
    # make a copy
    env = os.environ.copy()
    try:
        yield
    finally:
        # restore the environment variables
        # TODO: test this out, this seems blunt
        os.environ.clear()
        os.environ.update(env)
