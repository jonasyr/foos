"""Simple timestamp tracking utility used by plugins."""

import time


class Clock:
    """Track a named timestamp and provide helpers for elapsed time."""

    def __init__(self, name):
        """Create a clock instance.

        Args:
            name: Descriptive identifier used for logging and debugging.
        """

        self.name = name
        self.time = None

    def set(self, ts):
        """Store a specific timestamp."""

        self.time = ts

    def get(self):
        """Return the stored timestamp or ``None`` if unset."""

        return self.time

    def reset(self):
        """Update the clock to the current time."""

        self.time = time.time()

    def get_diff(self):
        """Return the number of seconds since the last :meth:`reset` call."""

        if self.time:
            return time.time() - self.time
        else:
            return None
