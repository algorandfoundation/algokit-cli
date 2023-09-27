from algokit_utils import Account

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


def test_transfer_no_option() -> None:
    result = invoke("task transfer")

    assert result.exit_code != 0
    verify(result.output)


def test_transfer_invalid_sender_accoount() -> None:
    result = invoke("task transfer -s invalid-address")

    assert result.exit_code != 0
    verify(result.output)


def test_transfer_invalid_receiver_accoount(sender_account: Account) -> None:
    result = invoke(f"task transfer -s {sender_account.address} -r invalid-address")

    assert result.exit_code != 0
    verify(result.output)


def test_transfer_no_amount(sender_account: Account, receiver_account: Account) -> None:
    result = invoke(f"task transfer -s {sender_account.address} -r {receiver_account.address} -a")

    assert result.exit_code != 0
    verify(result.output)


def test_transfer_algo(sender_account: Account, receiver_account: Account) -> None:
    result = invoke(f"task transfer -s {sender_account.address} -r {receiver_account.address} -a 1")

    assert result.exit_code != 0
    verify(result.output)


def test_transfer_asset(sender_account: Account, receiver_account: Account) -> None:
    result = invoke(f"task transfer -s {sender_account.address} -r {receiver_account.address} -a 1 -id 1")

    assert result.exit_code != 0
    verify(result.output)
