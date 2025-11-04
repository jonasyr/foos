"""Convenience module for loading project configuration overrides.

Importing this module pulls in the defaults from :mod:`config_base` and then
attempts to import a sibling :mod:`config` module that may contain local
overrides.  The approach mirrors the project's production deployment where a
``config.py`` file is generated on the device with site-specific settings.
"""

from config_base import *  # noqa: F401,F403 re-export configuration symbols

try:
    from config import *
except ImportError:
    pass
