import time
import queue
from threading import Thread

# Sentinel value to distinguish "not provided" from "explicitly None"
_DEFAULT = object()


def key(btns, state, duration, ev, ar):
    return {(frozenset(btns), state, duration): (ev, ar)}


def press(btns, state, short, long=_DEFAULT, ar=False):
    s = {}
    if short:
        s.update(key(btns, state, 'short', short, ar))
    # If long not specified, default to short. If long=None explicitly, skip long press
    if long is _DEFAULT:
        long = short
    if long is not None:
        s.update(key(btns, state, 'long', long, ar))

    return s


def up(btns, short, long=_DEFAULT):
    return press(btns, 'up', short, long, False)


def down(btns, short, long=_DEFAULT, ar=False):
    return press(btns, 'down', short, long, ar)


class Buttons:
    """Class to manage the state of the buttons and the needed logic"""

    def __init__(self, bus, enabled=True, long_press_delay=0.6):
        self.long_press_delay = long_press_delay
        self.queue = queue.Queue(maxsize=20)
        self.bus = bus
        self.bus.subscribe(self.enqueue, thread=False)
        self.buttons = frozenset([])
        self.last_time = 0
        self.press = 'short'
        self.enabled = enabled
        self.auto_repeat_interval = 0.2
        self.keymap = self.generateKeyMap()
        Thread(daemon=True, target=self.run).start()

    def enqueue(self, ev):
        try:
            self.queue.put_nowait(ev)
        except queue.Full:
            pass

    def checkState(self, state):
        keypress = (self.buttons, state, self.press)

        if keypress in self.keymap:
            ev, ar = self.keymap[keypress]
            self.bus.notify(*ev)

    def run(self):
        while True:
            while not self.queue.empty():
                ev = self.queue.get_nowait()
                self.process_event(ev)

            if len(self.buttons) > 0:
                now = time.time()
                diff = now - self.last_time

                state = 'down'
                keypress = (self.buttons, state, self.press)

                if keypress in self.keymap:
                    ev, ar = self.keymap[keypress]
                    if diff > self.auto_repeat_interval and ar:
                        self.checkState('down')
                        self.last_time = now

                # generate key press event
                if self.press == 'short' and diff > self.long_press_delay:
                    self.press = 'long'
                    self.checkState('down')

            time.sleep(0.01)

    def setEnabled(self, state):
        self.enabled = state
        self.clearState()

    def clearState(self):
        self.buttons = frozenset([])
        self.last_time = 0
        self.press = 'short'

    def process_event(self, ev):
        if not self.enabled or ev.data is None or 'state' not in ev.data:
            return

        button, state = (ev.data['btn'], ev.data['state'])

        now = time.time()
        if state == 'down':
            self.buttons = self.buttons.union([button])
            self.last_time = now
            # reset duration
            self.press = 'short'
            self.checkState(state)
            # For GPIO buttons (no UP event), clear state immediately to prevent accumulation
            if ev.data.get('source') == 'rpi':
                self.clearState()

        elif state == 'up':
            if button in self.buttons:
                self.checkState(state)
                # Delete all button events to avoid double processing (e.g. reset and one other key)
                self.clearState()
