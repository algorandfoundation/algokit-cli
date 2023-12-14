import codecs
import re
import socket
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

CLEAR_LINE = "\033[K"


def extract_version_triple(version_str: str) -> str:
    match = re.search(r"\d+\.\d+\.\d+", version_str)
    if not match:
        raise ValueError("Unable to parse version number")
    return match.group()


def is_minimum_version(system_version: str, minimum_version: str) -> bool:
    system_version_as_tuple = tuple(map(int, system_version.split(".")))
    minimum_version_as_tuple = tuple(map(int, minimum_version.split(".")))
    return system_version_as_tuple >= minimum_version_as_tuple


def is_network_available(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """
    Check if internet is available by trying to establish a socket connection.
    """

    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False


def animate(name: str, stop_event: threading.Event) -> None:
    spinner = {
        "interval": 100,
        "frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    }

    while not stop_event.is_set():
        for frame in spinner["frames"]:  # type: ignore  # noqa: PGH003
            if stop_event.is_set():
                break
            try:
                text = codecs.decode(frame, "utf-8")
            except Exception:
                text = frame
            output = f"\r{text} {name}"
            sys.stdout.write(output)
            sys.stdout.write(CLEAR_LINE)
            sys.stdout.flush()
            time.sleep(0.001 * spinner["interval"])  # type: ignore  # noqa: PGH003

    sys.stdout.write("\r ")


def run_with_animation(target_function: Callable[[], Any], animation_text: str = "Loading") -> Any:  # noqa: ANN401
    with ThreadPoolExecutor(max_workers=2) as executor:
        stop_event = threading.Event()
        animation_future = executor.submit(animate, animation_text, stop_event)
        function_future = executor.submit(target_function)

        try:
            result = function_future.result()
        except Exception as e:
            stop_event.set()
            animation_future.result()
            raise e
        else:
            stop_event.set()
            animation_future.result()
            return result
