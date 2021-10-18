class AGIException(Exception):
    """The base exception for all AGI-related exceptions.
    """

    def __init__(self, message, items):
        Exception.__init__(self, message)
        self.items = items  # A dictionary containing data received from Asterisk, if any


class AGIResultHangup(AGIException):
    """Indicates that Asterisk received a hangup event.
    """


class AGIError(AGIException):
    """The base exception for all AGI errors resulting from improper usage or Asterisk bug.
    """


class AGINoResultError(AGIError):
    """Indicates that Asterisk did not return a 'result' parameter in a 200 response.
    """


class AGIUnknownError(AGIError):
    """Indicates that an unknown response is received from Asterisk.
    """


class AGIAppError(AGIError):
    """Indicates that an Asterisk application failed to execute.
    """


class AGIDeadChannelError(AGIError):
    """Indicates that a command was issued on a channel that can no longer process it.
    """


class AGIInvalidCommand(AGIError):
    """Indicates that a request made to Asterisk was not understood.
    """


class AGIUsageError(AGIError):
    """Indicates that a request made to Asterisk was sent with invalid syntax.
    """
