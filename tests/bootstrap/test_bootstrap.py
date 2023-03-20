from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def test_bootstrap_help() -> None:
    result = invoke("bootstrap -h")

    assert result.exit_code == 0
    verify(result.output)
