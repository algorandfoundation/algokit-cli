from utils.approvals import verify
from utils.click_invoker import invoke


def test_bootstrap_help():
    result = invoke("bootstrap -h")

    assert result.exit_code == 0
    verify(result.output)
