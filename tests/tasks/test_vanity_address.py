import re
from pathlib import Path

import pytest

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


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
    result = invoke("task vanity-address A")

    assert result.exit_code == 0
    match = re.search(r"'address': '([^']+)'", result.output)
    if match:
        address = match.group(1)
        assert address.startswith("A")


def test_vanity_address_on_anywhere_match() -> None:
    result = invoke("task vanity-address A -m anywhere")

    assert result.exit_code == 0
    match = re.search(r"'address': '([^']+)'", result.output)
    if match:
        address = match.group(1)
        assert "A" in address


def test_vanity_address_on_file(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    output_file_path = Path(cwd) / "output.txt"
    result = invoke(f"task vanity-address A -o file -f {output_file_path}")

    assert result.exit_code == 0
    assert output_file_path.exists()
    output = output_file_path.read_text()

    # Ensure output address starts with A
    output_match = re.search(r'\"address\": "([^"]+)"', output)

    if output_match:
        address = output_match.group(1)
        assert address.startswith("A")
