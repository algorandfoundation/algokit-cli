from __future__ import annotations

import importlib
import sys
import typing as t

_TOML_MODULE = "tomllib" if sys.version_info >= (3, 11) else "tomli"
_toml = importlib.import_module(_TOML_MODULE)


def loads(data: str) -> dict[str, t.Any]:
    return t.cast("dict[str, t.Any]", _toml.loads(data))
