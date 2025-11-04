"""Helpers for discovering, instantiating and persisting plugin state."""

import os
import atexit
import pickle
import importlib
import logging
import foos.config as config

logger = logging.getLogger(__name__)


class PluginHandler:
    """Load configured plugins and manage their persisted state."""

    def __init__(self, bus):
        """Instantiate the handler and bootstrap plugins.

        Args:
            bus: Shared :class:`~foos.bus.Bus` instance used to deliver events to
                plugins.
        """

        self.status_file = '.status'
        # Register save status on exit
        atexit.register(self.save)
        self.load(bus)
        self.load_state()

    def load(self, bus):
        """Import and instantiate every plugin listed in configuration."""

        self.running_plugins = {}
        logger.info("Loading plugins %s", config.plugins)
        for plugin in config.plugins:
            module = importlib.import_module('plugins.' + plugin)
            p = module.Plugin(bus)
            self.running_plugins[plugin] = p
            logger.debug("Loaded plugin %s", plugin)

    def save(self):
        """Persist plugin state by invoking optional ``save`` hooks."""

        state = {}
        for name, p in self.running_plugins.items():
            m = getattr(p, "save", None)
            if callable(m):
                s = m()
                if s:
                    state[name] = s

        with open(self.status_file, 'wb') as f:
            pickle.dump(state, f)

    def load_state(self):
        """Restore plugin state from disk if a status file exists."""

        if not os.path.isfile(self.status_file):
            logger.info("Not loading state: State file not found")
            return
        try:
            with open(self.status_file, 'rb') as f:
                state = pickle.load(f)

                for name, s in state.items():
                    if name in self.running_plugins:
                        p = self.running_plugins[name]
                        m = getattr(p, "load", None)
                        if callable(m):
                            m(s)

        except Exception:  # pragma: no cover - defensive logging
            logger.exception("State loading failed")
