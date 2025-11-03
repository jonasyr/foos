from .buttons import *


class Plugin(Buttons):
    def __init__(self, bus):
        super().__init__(bus, long_press_delay=0.6)
        self.menu_visible = False

    def generateKeyMap(self):
        key_map = {}
        # Note: long=None prevents double-trigger after long_press_delay
        # Two-button combos (reset_score) removed - can't work with GPIO-only input
        for d in [down(['black_minus'], ('decrement_score', {'team': 'black'}), long=None),
                  down(['black_plus'], ('goal_event', {'team': 'black', 'source': 'rpi'}), long=None),
                  down(['yellow_minus'], ('decrement_score', {'team': 'yellow'}), long=None),
                  down(['yellow_plus'], ('goal_event', {'team': 'yellow', 'source': 'rpi'}), long=None)]:
            key_map.update(d)
        return key_map

    def process_event(self, ev):
        if ev.name == 'menu_visible':
            self.menu_visible = True
            self.setEnabled(False)
        elif ev.name == 'menu_hidden':
            self.menu_visible = False
            self.setEnabled(True)
        elif ev.name == 'button_event' and ev.data.get('btn') == 'ok' and self.enabled:
            # OK button short press opens menu (only when control is enabled = menu closed)
            self.bus.notify('menu_show', {})
        else:
            super().process_event(ev)
