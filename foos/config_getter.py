"""Command line helper for reading configuration attributes."""

import config
import sys
import collections.abc


def toString(value):
    """Convert a configuration value into a printable string.

    Nested iterables (such as lists or tuples) are flattened using spaces so the
    output remains shell-friendly when consumed by other scripts.

    Args:
        value: Arbitrary configuration value.

    Returns:
        String representation suitable for terminal output.
    """

    if isinstance(value, collections.abc.Iterable) and not isinstance(value, str):
        return(" ".join(map(toString, value)))
    else:
        return str(value)


if __name__ == "__main__":
    values = [toString(getattr(config, x)) for x in sys.argv[1:]]
    print(" ".join(values))
