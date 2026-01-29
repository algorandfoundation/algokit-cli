import re
from typing import Any

import approvaltests
from approvaltests.scrubbers.scrubbers import Scrubber, combine_scrubbers

from algokit.core.utils import CLEAR_LINE, SPINNER_FRAMES

__all__ = [
    "Scrubber",
    "TokenScrubber",
    "combine_scrubbers",
    "normalize_path",
    "verify",
]


def normalize_path(content: str, path: str, token: str) -> str:
    return re.sub(
        rf"{token}\S+",
        lambda m: m[0].replace("\\", "/"),
        content.replace(path, token).replace(path.replace("\\", "/"), token),
    )


def _normalize_platform_differences(data: str, poetry_version: str = "99.99.99") -> str:
    """Normalize platform-specific and version-specific differences."""
    result = data

    # Normalize Git error messages across platforms (Arch Linux vs others)
    result = re.sub(
        r"DEBUG: git: fatal: not a git repository \(or any parent up to mount point /\)",
        "DEBUG: git: fatal: not a git repository (or any of the parent directories): .git",
        result,
    )

    # Remove Arch Linux specific Git filesystem boundary message
    result = re.sub(
        r"DEBUG: git: Stopping at filesystem boundary \(GIT_DISCOVERY_ACROSS_FILESYSTEM not set\)\.\n", "", result
    )

    # Normalize Poetry version output to avoid test failures on version updates
    result = re.sub(
        r"DEBUG: poetry: Poetry \(version \d+\.\d+\.\d+\)", f"DEBUG: poetry: Poetry (version {poetry_version})", result
    )

    # Normalize msgpack/Python TypeError messages for 'in' operator
    # C-extension msgpack (Python 3.10-3.13) says "is not a container or iterable"
    # Pure-Python msgpack (Python 3.14+, no wheel available) uses native "is not iterable"
    result = re.sub(
        r"argument of type 'int' is not a container or iterable",
        "argument of type 'int' is not iterable",
        result,
    )

    return result


class TokenScrubber(Scrubber):  # type: ignore[misc]
    def __init__(self, tokens: dict[str, str]):
        self._tokens = tokens

    def __call__(self, data: str) -> str:
        result = data
        for token, search in self._tokens.items():
            result = result.replace(search, "{" + token + "}")

        # Normalize platform and version differences for consistent tests
        result = _normalize_platform_differences(result)

        # Normalize SPINNER_FRAMES
        for frame in SPINNER_FRAMES:
            result = result.replace(frame, "")
        # Normalize CLEAR_LINE
        return result.replace(CLEAR_LINE, " ")


def verify(
    data: Any,  # noqa: ANN401
    *,
    options: approvaltests.Options | None = None,
    scrubber: Scrubber | None = None,
    poetry_version: str = "99.99.99",
    **kwargs: Any,
) -> None:
    options = options or approvaltests.Options()
    if scrubber is not None:
        options = options.add_scrubber(scrubber)
    kwargs.setdefault("encoding", "utf-8")
    normalised_data = str(data).replace("\r\n", "\n")

    # Apply global platform/version normalization with configurable poetry version
    normalised_data = _normalize_platform_differences(normalised_data, poetry_version)

    approvaltests.verify(
        data=normalised_data,
        options=options,
        # Don't normalise newlines
        newline="",
        **kwargs,
    )
