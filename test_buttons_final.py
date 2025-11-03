#!/usr/bin/env python3
"""
Test script for 5-button GPIO implementation with debouncing and long-press.
Tests the actual io_raspberry plugin behavior.
"""

import sys
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

# Mock bus for testing
class MockBus:
    def __init__(self):
        self.events = []
        self.subscribers = {}
    
    def notify(self, event_type, data):
        """Capture bus events for verification."""
        self.events.append((event_type, data))
        logger.info("Bus event: %s - %s", event_type, data)
    
    def subscribe(self, callback, **kwargs):
        """Mock subscribe method for compatibility with IOBase."""
        # IOBase just subscribes a callback, no event_type specified
        pass

def main():
    logger.info("=" * 60)
    logger.info("5-Button GPIO Test (with debouncing & long-press)")
    logger.info("=" * 60)
    
    # Import config and plugin
    import config
    from plugins import io_raspberry
    
    # Display button mapping
    logger.info("\nButton mapping (BCM):")
    for name, pin in sorted(config.io_raspberry_pins.items()):
        logger.info("  %-15s GPIO %2d", name, pin)
    
    # Create mock bus and initialize plugin
    logger.info("\nInitializing GPIO plugin...")
    bus = MockBus()
    
    try:
        plugin = io_raspberry.Plugin(bus)
        logger.info("✓ Plugin initialized successfully")
    except Exception as e:
        logger.error("✗ Plugin initialization failed: %s", e)
        return 1
    
    logger.info("\n" + "=" * 60)
    logger.info("Test Instructions:")
    logger.info("=" * 60)
    logger.info("1. Press yellow_plus (GPIO 17) - should trigger goal + replay")
    logger.info("2. Press black_plus (GPIO 27) - should trigger goal + replay")
    logger.info("3. Press yellow_minus (GPIO 23) - should emit button event")
    logger.info("4. Press black_minus (GPIO 25) - should emit button event")
    logger.info("5. Short press OK (GPIO 5) - should trigger short replay")
    logger.info("6. Long press OK (GPIO 5, >0.9s) - should trigger long replay")
    logger.info("\nPress Ctrl+C to exit")
    logger.info("=" * 60 + "\n")
    
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("\n\nTest completed!")
        logger.info("Total events captured: %d", len(bus.events))
        
        # Summary
        goal_events = [e for e in bus.events if e[0] == 'goal_event']
        button_events = [e for e in bus.events if e[0] == 'button_event']
        replay_events = [e for e in bus.events if e[0] == 'replay_request']
        
        logger.info("\nEvent summary:")
        logger.info("  Goal events:    %d", len(goal_events))
        logger.info("  Button events:  %d", len(button_events))
        logger.info("  Replay requests: %d", len(replay_events))
        
        return 0

if __name__ == '__main__':
    sys.exit(main())
