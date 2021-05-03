""" OpenWPM Custom Errors """


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
