from .buttons import *


class Plugin(Buttons):
    def __init__(self, bus):
        super().__init__(bus, long_press_delay=0.6)
        self.menu_visible = False

    def generateKeyMap(self):
        key_map = {}
        for d in [up(['black_minus'], ('decrement_score', {'team': 'black'})),
                  up(['black_plus'], ('increment_score', {'team': 'black'})),
                  up(['yellow_minus'], ('decrement_score', {'team': 'yellow'})),
                  up(['yellow_plus'], ('increment_score', {'team': 'yellow'})),
                  # OK button handled in process_event (short=menu toggle, long=handled by replay_bridge)
                  up(['black_minus', 'black_plus'], ('reset_score', {}), long=None),
                  up(['yellow_minus', 'yellow_plus'], ('reset_score', {}), long=None),
                  down(['black_minus', 'black_plus'], None, long=('menu_show', {})),
                  down(['yellow_minus', 'yellow_plus'], None, long=('menu_show', {}))]:
            key_map.update(d)
        return key_map

    def process_event(self, ev):
        if ev.name == 'menu_visible':
            self.menu_visible = True
            self.setEnabled(False)
        elif ev.name == 'menu_hidden':
            self.menu_visible = False
            self.setEnabled(True)
        elif ev.name == 'button_event' and ev.data.get('btn') == 'ok':
            # OK button short press toggles menu
            if self.menu_visible:
                self.bus.notify('menu_hide', {})
            else:
                self.bus.notify('menu_show', {})
        else:
            super().process_event(ev)
