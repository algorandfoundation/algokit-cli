import codecs
import re
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import cursor

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


def decode_utf_8_text(text: str) -> bytes | str:
    try:
        return codecs.decode(text, "utf-8")
    except Exception:
        return text


def animate(name: str, style: str, stop_event: threading.Event) -> None:
    spinners = {
        "dots": {"interval": 100, "frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]},
        "simpleDotsScrolling": {"interval": 200, "frames": [".  ", ".. ", "...", " ..", "  .", "   "]},
    }
    frames = spinners[style]["frames"]
    interval = spinners[style]["interval"]
    while not stop_event.is_set():
        for frame in frames:
            if stop_event.is_set():
                break
            the_frame = decode_utf_8_text(frame)
            output = f"\r{the_frame} {name}"
            sys.stdout.write(output)
            sys.stdout.write(CLEAR_LINE)
            sys.stdout.flush()
            time.sleep(0.001 * interval)

    sys.stdout.write("\rLoading complete!\n")


def run_with_animation(target_function, animation_text="Loading", spinner_style="dots", *args, **kwargs):
    with ThreadPoolExecutor(max_workers=2) as executor:
        stop_event = threading.Event()
        animation_future = executor.submit(animate, animation_text, spinner_style, stop_event)
        function_future = executor.submit(target_function, *args, **kwargs)

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
