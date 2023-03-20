from approvaltests import verify

from tests.utils.click_invoker import invoke


def test_localnet_help() -> None:
    result = invoke("localnet -h")

    assert result.exit_code == 0
    verify(result.output)
