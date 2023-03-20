from approvaltests import verify

from tests.utils.click_invoker import invoke


def test_help() -> None:
    result = invoke("-h")

    assert result.exit_code == 0
    verify(result.output)


def test_version() -> None:
    result = invoke("--version")

    assert result.exit_code == 0
