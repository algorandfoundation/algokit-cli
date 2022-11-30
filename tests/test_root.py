from approvaltests import verify  # type: ignore
from utils.click_invoker import invoke


def test_help():
    result = invoke("-h")

    assert result.exit_code == 0
    verify(result.output)
