import re

import pytest

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def test_vanity_address_help() -> None:
    result = invoke("task vanity-address -h")

    assert result.exit_code == 0
    verify(result.output)


def test_vanity_address_no_options() -> None:
    result = invoke("task vanity-address")

    assert result.exit_code != 0
    verify(result.output)


def test_vanity_address_invalid_keyword() -> None:
    result = invoke("task vanity-address test")

    assert result.exit_code != 0
    verify(result.output)


def test_vanity_address_invalid_input_on_file() -> None:
    result = invoke("task vanity-address TEST -o file")

    assert result.exit_code != 0
    verify(result.output)


def test_vanity_address_invalid_input_on_alias() -> None:
    result = invoke("task vanity-address TEST -o alias")

    assert result.exit_code != 0
    verify(result.output)


def test_vanity_address_on_default() -> None:
    result = invoke("task vanity-address T")

    assert result.exit_code == 0
    match = re.search(r"'address': '([^']+)'", result.output)
    if match:
        address = match.group(1)
        assert address.startswith("T")


def test_vanity_address_on_anywhere_match() -> None:
    result = invoke("task vanity-address T -m anywhere")

    assert result.exit_code == 0
    match = re.search(r"'address': '([^']+)'", result.output)
    if match:
        address = match.group(1)
        assert "T" in address


def test_vanity_address_on_file(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    result = invoke(f"task vanity-address T -o file -f {cwd}/output.txt")

    assert result.exit_code == 0
    assert (cwd / "output.txt").exists()

    with (cwd / "output.txt").open() as f:
        output = f.read()

    ouput_match = re.search(r"'address': '([^']+)'", output)
    if ouput_match:
        address = ouput_match.group(1)
        assert address.startswith("T")
