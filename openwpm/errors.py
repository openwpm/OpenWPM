"""OpenWPM Custom Errors"""


class CommandExecutionError(Exception):
    """Raise for errors related to executing commands"""

    def __init__(self, message, command, *args):
        self.message = message
        self.command = command
        super(CommandExecutionError, self).__init__(message, command, *args)


class ProfileLoadError(Exception):
    """Raise for errors that occur while loading profile"""

    def __init__(self, message, *args):
        self.message = message
        super(ProfileLoadError, self).__init__(message, *args)


class BrowserConfigError(Exception):
    """Raise for errors that occur from a misconfiguration of the browser"""

    def __init__(self, message, *args):
        self.message = message
        super(BrowserConfigError, self).__init__(message, *args)


class ConfigError(Exception):
    """Raise for errors that occur from a misconfiguration of the browser and manager params"""

    def __init__(self, message, *args):
        self.message = message
        super(ConfigError, self).__init__(message, *args)


class BrowserCrashError(Exception):
    """Raise for non-critical crashes within the BrowserManager process"""

    def __init__(self, message, *args):
        self.message = message
        super(BrowserCrashError, self).__init__(message, *args)


class ConstraintViolation(Exception):
    """A record could not be stored because it tripped the storage schema.

    This is a *data* fault, not an infrastructure fault: a NOT-NULL / primary
    key / unique / type / unknown-column / schema mismatch on a specific
    record. Per the data-failure policy (crosslink #46) a constraint violation
    means a page found a way to trip our schema and the affected visit must be
    failed and surfaced for manual investigation -- NOT silently dropped and
    NOT retried (retrying a malformed record can never succeed).

    Storage providers raise this from ``store_record`` (or while turning a
    record into a batch) so the ``StorageController`` can fail the owning visit
    with an investigable error. Distinguish from a *transient* storage error (a
    write/flush blip), which is any other exception and is retried.

    Attributes
    ----------
    table
        The table whose schema was tripped.
    visit_id
        The visit that owns the offending record.
    reason
        A short, human-readable description of which constraint was tripped
        (e.g. the underlying DB error). Kept concise and PII/size-aware -- it is
        logged and must be safe to surface.
    """

    def __init__(
        self,
        message: str,
        *,
        table: str,
        visit_id: int,
        reason: str,
    ) -> None:
        self.message = message
        self.table = table
        self.visit_id = visit_id
        self.reason = reason
        super().__init__(message)
