from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture
from utils.approvals import verify
from utils.click_invoker import invoke

FAKE_NOW = datetime(2020, 3, 11, 14, 0, 0)


@pytest.fixture(autouse=True)
def test_time_now(mocker: MockerFixture):
    mock_date = mocker.patch("algokit.core.doctor.datetime")
    fake_now = datetime(1990, 12, 31, 14, 0, 0, tzinfo=timezone.utc)
    mock_date.now.return_value = fake_now


def test_doctor_help(mocker: MockerFixture):
    result = invoke("doctor -h")

    assert result.exit_code == 0
    verify(result.output)


def test_doctor_default(mocker: MockerFixture):
    result = invoke("doctor")

    assert result.exit_code == 0
    verify(result.output)
