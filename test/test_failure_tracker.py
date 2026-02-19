import pytest

from openwpm.failure_tracker import CommandFailure, FailureTracker
from openwpm.types import BrowserId

pytestmark = pytest.mark.pyonly


def _failure() -> CommandFailure:
    return CommandFailure(
        browser_id=BrowserId(0), command="GetCommand", command_status="error"
    )


def test_limit_is_exceeded_only_past_failure_limit() -> None:
    tracker = FailureTracker(failure_limit=2)
    assert tracker.record_failure(_failure()) is False
    assert tracker.record_failure(_failure()) is False
    assert tracker.record_failure(_failure()) is True


def test_reset_clears_consecutive_failures() -> None:
    tracker = FailureTracker(failure_limit=1)
    tracker.record_failure(_failure())
    tracker.reset()
    assert tracker.failures == []
    assert tracker.record_failure(_failure()) is False
