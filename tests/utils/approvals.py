import re
from typing import Any

import approvaltests
from approvaltests.scrubbers.scrubbers import Scrubber, combine_scrubbers

__all__ = [
    "TokenScrubber",
    "Scrubber",
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


class TokenScrubber(Scrubber):  # type: ignore[misc]
    def __init__(self, tokens: dict[str, str]):
        self._tokens = tokens

    def __call__(self, data: str) -> str:
        result = data
        for token, search in self._tokens.items():
            result = result.replace(search, "{" + token + "}")
        return result


def verify(
    data: Any,  # noqa: ANN401
    *,
    options: approvaltests.Options | None = None,
    scrubber: Scrubber | None = None,
    **kwargs: Any,
) -> None:
    options = options or approvaltests.Options()
    if scrubber is not None:
        options = options.add_scrubber(scrubber)
    kwargs.setdefault("encoding", "utf-8")
    normalised_data = str(data).replace("\r\n", "\n")
    approvaltests.verify(
        data=normalised_data,
        options=options,
        # Don't normalise newlines
        newline="",
        **kwargs,
    )
