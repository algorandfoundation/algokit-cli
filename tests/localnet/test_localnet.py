from approvaltests import verify  # type: ignore
from utils.click_invoker import invoke


def test_localnet_help():
    result = invoke("localnet -h")

    assert result.exit_code == 0
    verify(result.output)
