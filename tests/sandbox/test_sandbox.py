from approvaltests import verify  # type: ignore
from utils.click_invoker import invoke


def test_sandbox_help():
    result = invoke("sandbox -h")

    assert result.exit_code == 0
    verify(result.output)
