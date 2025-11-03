import time
import logging
import RPi.GPIO as GPIO
from .io_base import IOBase
import foos.config as config

logger = logging.getLogger(__name__)

class Plugin(IOBase):
    """
    5-button GPIO input plugin for Raspberry Pi.
    All buttons are active-low (connect to GND) with internal pull-ups.
    """
    
    def __init__(self, bus):
        self.bus = bus
        self.pin_to_name = {}  # Map GPIO pin number to logical button name
        self.ok_button_processing = False  # Flag to prevent double-fire on OK button
        
        # Clean up any previous GPIO state
        try:
            GPIO.setmode(GPIO.BCM)
            # Remove any existing event detection on our pins
            for pin in config.io_raspberry_pins.values():
                try:
                    GPIO.remove_event_detect(pin)
                except:
                    pass
        except:
            pass
        
        # Set BCM numbering mode
        GPIO.setmode(GPIO.BCM)
        
        # Setup all GPIO pins with pull-ups
        for name, pin in config.io_raspberry_pins.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.pin_to_name[pin] = name
            logger.info("GPIO setup: %s on pin %d (BCM)", name, pin)
        
        # Register +/- buttons with standard debounce (300ms)
        for name, pin in config.io_raspberry_pins.items():
            if name.endswith('_plus') or name.endswith('_minus'):
                try:
                    GPIO.add_event_detect(pin, GPIO.FALLING, 
                                        callback=self._score_button_callback, 
                                        bouncetime=300)
                    logger.info("Registered score button: %s (pin %d, debounce 300ms)", name, pin)
                except RuntimeError as e:
                    # This shouldn't happen after cleanup, but log and re-raise
                    logger.error("Failed to register pin %d (%s): %s", pin, name, e)
                    raise
        
        # Register OK button with long-press detection (600ms debounce)
        ok_pin = config.io_raspberry_pins['ok_button']
        try:
            GPIO.add_event_detect(ok_pin, GPIO.FALLING, 
                                callback=self._ok_button_callback, 
                                bouncetime=600)
            logger.info("Registered OK button: pin %d (debounce 600ms, long-press enabled)", ok_pin)
        except RuntimeError as e:
            # This shouldn't happen after cleanup, but log and re-raise
            logger.error("Failed to register OK button pin %d: %s", ok_pin, e)
            raise
        
        super().__init__(bus)
    
    def _score_button_callback(self, channel):
        """
        Handle +/- button presses.
        Maps GPIO pin to button name and emits appropriate bus events.
        """
        name = self.pin_to_name.get(channel)
        if not name:
            logger.warning("Unknown GPIO pin %d triggered", channel)
            return
        
        logger.info("Button pressed: %s (pin %d)", name, channel)
        
        # Parse button name to determine team and action
        # Format: "yellow_plus", "yellow_minus", "black_plus", "black_minus"
        parts = name.split('_')
        if len(parts) != 2:
            logger.warning("Invalid button name format: %s", name)
            return
        
        team = parts[0]  # "yellow" or "black"
        action = parts[1]  # "plus" or "minus"
        
        # Emit button event for general handling
        event_data = {
            'source': 'rpi',
            'btn': name,
            'state': 'down',
            'team': team,
            'action': action
        }
        self.bus.notify('button_event', event_data)
        
        # Emit goal event for +1 buttons (triggers scoring and replay)
        if action == 'plus':
            logger.info("Goal for team %s!", team)
            self.bus.notify('goal_event', {'source': 'rpi', 'team': team})
    
    def _ok_button_callback(self, channel):
        """
        Handle OK button with long-press detection.
        Short press (<0.9s): trigger short replay
        Long press (≥0.9s): trigger long replay
        """
        # Prevent concurrent execution (ignore if already processing)
        if self.ok_button_processing:
            return
        
        self.ok_button_processing = True
        
        try:
            name = self.pin_to_name.get(channel, 'ok_button')
            logger.info("OK button pressed (pin %d)", channel)
            
            # Measure press duration
            t0 = time.monotonic()
            
            # Wait for button release or timeout (max 2 seconds)
            timeout = 2.0
            while GPIO.input(channel) == GPIO.LOW and (time.monotonic() - t0) < timeout:
                time.sleep(0.01)
            
            press_duration = time.monotonic() - t0
            
            # Wait for button to be fully released and settle
            time.sleep(0.15)
            
            # Determine replay type based on press duration
            if press_duration >= 0.9:
                replay_kind = 'long'
                logger.info("Long press detected (%.2fs) - triggering long replay", press_duration)
            else:
                replay_kind = 'short'
                logger.info("Short press detected (%.2fs) - triggering short replay", press_duration)
            
            # Emit button event
            event_data = {
                'source': 'rpi',
                'btn': name,
                'state': 'down',
                'press_duration': press_duration
            }
            self.bus.notify('button_event', event_data)
            
            # Emit replay request
            self.bus.notify('replay_request', {'kind': replay_kind})
            
        finally:
            # Always release the lock
            self.ok_button_processing = False

    def reader_thread(self):
        """GPIO events are handled via callbacks, no polling needed."""
        while True:
            time.sleep(1)
    
    def writer_thread(self):
        """No GPIO output needed for button-only input."""
        while True:
            line = self.write_queue.get()
            time.sleep(1)
    
    def __del__(self):
        """Cleanup GPIO resources on plugin shutdown."""
        try:
            # Remove all event detection
            for pin in config.io_raspberry_pins.values():
                try:
                    GPIO.remove_event_detect(pin)
                except:
                    pass
            logger.info("GPIO cleanup completed")
        except:
            pass
