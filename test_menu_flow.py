#!/usr/bin/env python3
"""
Debug menu and control interaction.
Monitor all button and menu events to understand the flow.
"""

import sys
import time
from multiprocessing import Queue

class Event:
    def __init__(self, name, data):
        self.name = name
        self.data = data

class DebugBus:
    def __init__(self):
        self.events = []
        self.subscribers = {}
    
    def notify(self, name, data):
        timestamp = time.time()
        self.events.append((timestamp, name, data))
        print(f"[{timestamp:.3f}] 📤 {name}: {data}")
        
        # Call subscribers
        if name in self.subscribers:
            for callback in self.subscribers[name]:
                try:
                    callback(Event(name, data))
                except Exception as e:
                    print(f"  ❌ Subscriber error: {e}")
    
    def subscribe_map(self, event_map, owner=None, thread=False):
        for event_name, callback in event_map.items():
            if event_name not in self.subscribers:
                self.subscribers[event_name] = []
            self.subscribers[event_name].append(callback)

# Create debug bus
bus = DebugBus()

# Import plugins
from plugins.control import Plugin as ControlPlugin
from plugins.menu import Plugin as MenuPlugin

print("=" * 70)
print("Debug: Menu and Control Interaction")
print("=" * 70)

# Initialize plugins
print("\n1. Initializing plugins...")
control = ControlPlugin(bus)
menu = MenuPlugin(bus)

print(f"   Control: enabled={control.enabled}, menu_visible={control.menu_visible}")
print(f"   Menu: enabled={menu.enabled}")

# Simulate button press: OK (open menu)
print("\n2. Simulating OK button press (menu closed)...")
ok_event = Event('button_event', {'btn': 'ok', 'state': 'down', 'source': 'rpi'})
control.process_event(ok_event)
time.sleep(0.1)

# Check last event
if bus.events:
    last_event = bus.events[-1]
    print(f"   Last event: {last_event[1]}")
    if last_event[1] == 'menu_show':
        print("   ✅ Menu show event emitted")
        
        # Simulate UI responding
        print("\n3. Simulating UI response: menu_visible...")
        menu_visible_event = Event('menu_visible', {})
        control.process_event(menu_visible_event)
        menu.process_event(menu_visible_event)
        
        print(f"   Control: enabled={control.enabled}, menu_visible={control.menu_visible}")
        print(f"   Menu: enabled={menu.enabled}")

# Simulate navigation: yellow_minus (menu down)
print("\n4. Simulating yellow_minus button press (navigate down)...")
nav_event = Event('button_event', {'btn': 'yellow_minus', 'state': 'down', 'source': 'rpi'})
control.process_event(nav_event)
menu.process_event(nav_event)
time.sleep(0.4)  # Wait past long_press_delay

# Check how many menu_down events
menu_down_count = sum(1 for _, name, _ in bus.events if name == 'menu_down')
print(f"   menu_down events: {menu_down_count}")
if menu_down_count == 1:
    print("   ✅ Single menu_down (no double-trigger)")
elif menu_down_count == 2:
    print("   ❌ DOUBLE-TRIGGER detected!")
else:
    print(f"   ❓ Unexpected count: {menu_down_count}")

# Simulate OK button press to select (which might be "Back")
print("\n5. Simulating OK button press (select menu item)...")
select_event = Event('button_event', {'btn': 'ok', 'state': 'down', 'source': 'rpi'})
control.process_event(select_event)
menu.process_event(select_event)
time.sleep(0.1)

# Check if menu_select was emitted
menu_select_count = sum(1 for _, name, _ in bus.events if name == 'menu_select')
print(f"   menu_select events: {menu_select_count}")
if menu_select_count == 1:
    print("   ✅ Menu select emitted")
else:
    print(f"   ❌ Expected 1 menu_select, got {menu_select_count}")

# Simulate "Back" being selected (emits menu_hide)
print("\n6. Simulating 'Back' selection (menu_hide)...")
bus.notify('menu_hide', {})
time.sleep(0.1)

# Simulate UI responding
print("\n7. Simulating UI response: menu_hidden...")
menu_hidden_event = Event('menu_hidden', {})
control.process_event(menu_hidden_event)
menu.process_event(menu_hidden_event)

print(f"   Control: enabled={control.enabled}, menu_visible={control.menu_visible}")
print(f"   Menu: enabled={menu.enabled}")

if control.enabled and not menu.enabled:
    print("   ✅ Plugins returned to correct state")
else:
    print("   ❌ Plugin state incorrect!")

# Try button press after menu closed
print("\n8. Simulating yellow_plus after menu closed (should trigger goal)...")
goal_event = Event('button_event', {'btn': 'yellow_plus', 'state': 'down', 'source': 'rpi'})
control.process_event(goal_event)
menu.process_event(goal_event)
time.sleep(0.1)

# Check if goal_event was emitted
goal_event_count = sum(1 for _, name, _ in bus.events if name == 'goal_event')
if goal_event_count > 0:
    print(f"   ✅ goal_event emitted ({goal_event_count} times)")
else:
    print("   ❌ No goal_event emitted!")

print("\n" + "=" * 70)
print("Event Timeline:")
print("=" * 70)
for timestamp, name, data in bus.events:
    print(f"[{timestamp:.3f}] {name}: {data}")

print("\n✅ Debug test complete!")
