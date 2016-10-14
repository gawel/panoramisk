__all__ = ('DisconnectedError', )


class DisconnectedError(BrokenPipeError):
    """Disconnected."""
    def __init__(self, action):
        self.action = action
