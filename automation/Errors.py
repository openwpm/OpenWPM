""" OpenWPM Custom Errors """

class CommandExecutionError(Exception):
    """ Raise for errors related to executing commands """
    def __init__(self, message, command, *args):
        self.message = message
        self.command = command
        super(CommandExecutionError, self).__init__(message, command, *args)
