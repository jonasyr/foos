from .buttons import *


class Plugin(Buttons):
    def __init__(self, bus):
        super().__init__(bus, long_press_delay=0.6)
        self.menu_visible = False

    def generateKeyMap(self):
        key_map = {}
        for d in [down(['black_minus'], ('decrement_score', {'team': 'black'})),
                  down(['black_plus'], ('goal_event', {'team': 'black', 'source': 'rpi'})),
                  down(['yellow_minus'], ('decrement_score', {'team': 'yellow'})),
                  down(['yellow_plus'], ('goal_event', {'team': 'yellow', 'source': 'rpi'})),
                  # OK button handled in process_event (short=menu toggle, long=handled by replay_bridge)
                  down(['black_minus', 'black_plus'], None, long=('reset_score', {})),
                  down(['yellow_minus', 'yellow_plus'], None, long=('reset_score', {}))]:
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
