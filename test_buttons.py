#!/usr/bin/env python3
"""Test script for foosball buttons (5-button setup)"""
import RPi.GPIO as GPIO
import time
import sys

# Button configuration from config.py
# Note: Yellow/Black Goal buttons act as +1, so separate +1 buttons are not needed
BUTTONS = {
    "Yellow Goal/+1": 17,
    "Black Goal/+1": 27,
    "Yellow -1": 23,
    "Black -1": 25,
    "OK Button": 5,
}

# Track button states
button_states = {pin: True for pin in BUTTONS.values()}  # True = not pressed (pulled up)
press_times = {pin: None for pin in BUTTONS.values()}

def get_button_name(pin):
    for name, p in BUTTONS.items():
        if p == pin:
            return name
    return f"GPIO {pin}"

def button_callback(channel):
    """Handle button press/release"""
    current_state = GPIO.input(channel)
    button_name = get_button_name(channel)
    
    if current_state == 0:  # Pressed (LOW)
        press_times[channel] = time.time()
        print(f"✓ [{button_name}] PRESSED")
    else:  # Released (HIGH)
        if press_times[channel]:
            duration = time.time() - press_times[channel]
            if duration > 2.0:
                print(f"  [{button_name}] LONG PRESS ({duration:.1f}s) - Menu/Upload action")
            else:
                print(f"  [{button_name}] SHORT PRESS ({duration:.2f}s)")
            press_times[channel] = None

def main():
    print("=" * 60)
    print("5-Button Test Script for Foosball Table")
    print("=" * 60)
    print("\nConfigured buttons:")
    for name, pin in sorted(BUTTONS.items(), key=lambda x: x[1]):
        print(f"  {name:20} → GPIO {pin:2} (Physical pin {get_physical_pin(pin)})")
    print("\nPress buttons to test. Press Ctrl+C to exit.\n")
    
    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    
    # Setup all buttons
    for pin in BUTTONS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.BOTH, callback=button_callback, bouncetime=50)
    
    try:
        # Keep running
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)
    finally:
        GPIO.cleanup()

def get_physical_pin(bcm_pin):
    """Convert BCM pin to physical pin number"""
    bcm_to_physical = {
        17: 11, 27: 13, 22: 15, 23: 16, 24: 18, 25: 22, 5: 29
    }
    return bcm_to_physical.get(bcm_pin, "?")

if __name__ == "__main__":
    main()
