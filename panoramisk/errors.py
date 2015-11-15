__all__ = ('DisconnectedError', )


class DisconnectedError(Exception):
    """Disconnected."""
    def __init__(self, action):
        self.action = action
