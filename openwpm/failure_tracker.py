"""Tracks command execution failures and determines when to halt crawling.

There are two failure mechanisms:

1. **Consecutive failure tracking** — Each non-ok command status is recorded
   via ``record_failure``.  After a successful command sequence the list is
   cleared.  When the number of recorded failures exceeds ``failure_limit``
   the tracker escalates to a critical failure.

2. **Critical failure** — An immediate halt signal set by
   ``set_critical_failure``.  Three situations trigger this:
   - A browser process sends a CRITICAL status (``CriticalChildException``).
   - The consecutive failure limit is exceeded (``ExceedCommandFailureLimit``).
   - A browser fails to relaunch (``ExceedLaunchFailureLimit``).
"""

import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .command_sequence import CommandSequence
from .types import BrowserId


@dataclass(frozen=True)
class CommandFailure:
    """A single command execution failure.

    Attributes
    ----------
    browser_id
        The browser that experienced the failure.
    command
        Human-readable representation of the command that failed.
    command_status
        The status string reported by the browser process
        (e.g. ``"timeout"``, ``"error"``, ``"neterror"``).
    error
        Optional error message extracted from the browser process.
    traceback
        Optional JSON-encoded traceback from the browser process.
    """

    browser_id: BrowserId
    command: str
    command_status: str
    error: Optional[str] = None
    traceback: Optional[str] = None


class FailureTracker:
    """Thread-safe tracker for command execution failures.

    Used by ``BrowserManagerHandle`` to report failures without needing a
    direct reference to ``TaskManager``.  The ``TaskManager`` checks
    ``has_critical_failure`` periodically and shuts down if it is set.

    The recorded ``failures`` list preserves context across consecutive
    failures so that common causes can be identified (e.g. all failures
    from the same browser, or all the same error type).
    """

    def __init__(self, failure_limit: int) -> None:
        self.failure_limit = failure_limit
        self.failures: List[CommandFailure] = []
        self.critical_failure: Optional[Dict[str, Any]] = None
        self.lock = threading.Lock()

    def record_failure(self, failure: CommandFailure) -> bool:
        """Record a command failure.

        Returns ``True`` when the number of consecutive failures exceeds
        ``failure_limit``, indicating that the crawl should be halted.
        """
        with self.lock:
            self.failures.append(failure)
            return len(self.failures) > self.failure_limit

    def reset(self) -> None:
        """Clear recorded failures after a successful command sequence."""
        with self.lock:
            self.failures.clear()

    def set_critical_failure(
        self,
        error_type: str,
        command_sequence: CommandSequence,
        exception: Optional[bytes] = None,
    ) -> None:
        """Record a critical failure that should halt crawling immediately.

        Parameters
        ----------
        error_type
            One of ``"CriticalChildException"``,
            ``"ExceedCommandFailureLimit"``, or
            ``"ExceedLaunchFailureLimit"``.
        command_sequence
            The command sequence that triggered the failure.
        exception
            Pickled exception info for ``CriticalChildException``.
        """
        status: Dict[str, Any] = {
            "ErrorType": error_type,
            "CommandSequence": command_sequence,
        }
        if exception is not None:
            status["Exception"] = exception
        self.critical_failure = status

    @property
    def has_critical_failure(self) -> bool:
        """Check if a critical failure has been recorded."""
        return self.critical_failure is not None
