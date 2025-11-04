#!/usr/bin/python3
"""Event bus implementation used to decouple plugins and UI components.

The :class:`Bus` class exposes a lightweight publish/subscribe mechanism backed
by a multiprocessing queue.  Plugins can subscribe to events and optionally
handle them on dedicated threads, while producers simply publish events without
needing to know who will handle them.  The small :class:`Event` container keeps
track of payload metadata for debugging and replay purposes.
"""

from threading import Thread
import queue
import time
import multiprocessing as mp
import logging

logger = logging.getLogger(__name__)


class Event:
    """Container for messages flowing through the :class:`Bus`.

    Attributes:
        name: String identifier for the event type.
        data: Arbitrary payload associated with the event.
        ts: Unix timestamp representing when the event was created.
    """

    def __init__(self, name, data=None, ts=None):
        self.name = name
        self.data = data
        self.ts = ts if ts is not None else time.time()

    def __repr__(self):
        return "Ev %s (%s)" % (self.name, repr(self.data))


class Bus:
    """In-process message bus for plugin communication.

    The bus spins up a background thread that forwards events from an internal
    ``multiprocessing.Queue`` to registered subscribers.  Consumers can opt in to
    threaded delivery to prevent long running handlers from blocking the main
    dispatch loop.
    """

    def __init__(self):
        """Initialize the bus and start the dispatcher thread."""

        self.queue = mp.Queue()
        self.subscribers = []
        Thread(target=self.__run, daemon=True).start()

    def subscribe_map(self, fmap, thread=False):
        """Subscribe handlers for multiple event names at once.

        Args:
            fmap: Mapping of event names to callables.  Each callable receives
                the event payload as its only argument.
            thread: When true each event is delivered on a worker thread to
                avoid blocking the bus.
        """

        def f(ev):
            fmap[ev.name](ev.data)

        self.subscribe(f, thread=thread, subscribed_events=fmap.keys())

    def subscribe(self, f, thread=False, subscribed_events=None):
        """Register a subscriber.

        Args:
            f: Callable receiving an :class:`Event` instance.
            thread: When true, the callable is invoked from a dedicated worker
                thread backed by an internal queue.
            subscribed_events: Optional iterable of event names.  When provided
                the handler receives only matching events.
        """

        if thread:
            f = self.__threaded_func(f, subscribed_events)

        def fs(ev):
            if ev.name in subscribed_events:
                f(ev)

        self.subscribers.append(fs if subscribed_events else f)

    def notify(self, ev, ev_data=None):
        """Publish an event to every subscriber.

        Args:
            ev: Name of the event to publish.
            ev_data: Arbitrary payload delivered to subscribers.
        """

        self.queue.put(Event(ev, ev_data))

    def __threaded_func(self, f, subscribed_events=None):
        """Wrap a subscriber to deliver messages asynchronously.

        Args:
            f: Callable that processes :class:`Event` objects.
            subscribed_events: Optional iterable of event names used for
                filtering at enqueue time.

        Returns:
            Callable that enqueues events for background processing.
        """

        q = queue.Queue(maxsize=20)

        def trun():
            while True:
                ev = q.get()
                try:
                    f(ev)
                except Exception:  # pragma: no cover - defensive logging
                    logger.exception("Error delivering event")
                finally:
                    q.task_done()

        def fthread(ev):
            try:
                if subscribed_events is None or ev.name in subscribed_events:
                    q.put_nowait(ev)

            except queue.Full:
                logger.warning("Queue full when sending %s to %s", ev.name, f)

        Thread(target=trun, daemon=True).start()
        return fthread

    def __run(self):
        """Continuously forward events from the queue to subscribers."""

        while True:
            e = self.queue.get()
            for s in self.subscribers:
                s(e)


if __name__ == '__main__':
    from functools import partial

    def log(*args):
        args = (time.time(),) + args
        print(*args)

    def logAndSleep(*args):
        l = args[1:]
        time.sleep(args[0])
        log(*l)

    b = Bus()
    b.subscribe(partial(log, 'sub_1'))
    b.subscribe(partial(logAndSleep, 1, 'sub_2'), thread=True)
    b.subscribe(partial(log, 'sub_3'))
    b.notify("a")
    b.notify("b")
    log("finished notifying")
    time.sleep(10)
