#!/usr/bin/env python3
"""
Quick test script to verify stats_event_logger plugin loads correctly.
This doesn't test network connectivity, just import and basic initialization.

Run from the foos directory:
    python3 plugins/test_stats_logger.py
"""

import sys
import os

# Add parent directory to path so we can import foos modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import():
    """Test that the plugin can be imported."""
    print("Testing plugin import...")
    try:
        from plugins import stats_event_logger
        print("✓ Plugin imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import plugin: {e}")
        return False

def test_initialization():
    """Test that the plugin can be initialized with a mock bus."""
    print("\nTesting plugin initialization...")
    try:
        from plugins.stats_event_logger import Plugin
        
        # Create a minimal mock bus
        class MockBus:
            def subscribe_map(self, fmap, thread=False):
                print(f"  - Subscribed to events: {', '.join(fmap.keys())}")
            
            def notify(self, event_name, data):
                pass
        
        bus = MockBus()
        plugin = Plugin(bus)
        
        print("✓ Plugin initialized successfully")
        print(f"  - Initial state: active={plugin.active}, events={len(plugin.events)}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize plugin: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_event_tracking():
    """Test basic event tracking without network calls."""
    print("\nTesting event tracking...")
    try:
        from plugins.stats_event_logger import Plugin
        
        class MockBus:
            def subscribe_map(self, fmap, thread=False):
                pass
            def notify(self, event_name, data):
                pass
        
        bus = MockBus()
        plugin = Plugin(bus)
        
        # Simulate match start
        plugin.on_match_start({})
        print(f"  - After match start: active={plugin.active}")
        
        # Simulate some goals
        plugin.on_goal({'team': 'yellow'})
        plugin.on_goal({'team': 'black'})
        plugin.on_goal({'team': 'yellow'})
        
        print(f"  - After 3 goals: events={len(plugin.events)}, Y:{plugin.score_y} B:{plugin.score_b}")
        
        # Verify event structure
        if plugin.events:
            first_event = plugin.events[0]
            expected_keys = {'team', 't', 'score_yellow', 'score_black'}
            if expected_keys.issubset(first_event.keys()):
                print(f"  - Event structure correct: {first_event}")
            else:
                print(f"  ✗ Event structure incorrect, missing keys: {expected_keys - set(first_event.keys())}")
                return False
        
        # Test decrement
        plugin.on_decrement({'team': 'yellow'})
        print(f"  - After decrement: Y:{plugin.score_y} B:{plugin.score_b}")
        
        print("✓ Event tracking works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Event tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Check if config has the required settings."""
    print("\nChecking configuration...")
    try:
        import foos.config as config
        
        required_settings = ['league_url', 'league_apikey', 'league_season']
        missing = []
        
        for setting in required_settings:
            if hasattr(config, setting):
                value = getattr(config, setting)
                placeholder = '<YOUR-' in str(value) or '<YOUR-KEY>' in str(value)
                status = "⚠ (placeholder)" if placeholder else "✓"
                print(f"  {status} {setting} = {value}")
            else:
                missing.append(setting)
                print(f"  ✗ {setting} = NOT SET")
        
        if missing:
            print(f"\n⚠ Missing configuration: {', '.join(missing)}")
            print("  Add these to config.py before using the plugin")
            return False
        else:
            print("\n✓ All required settings present (update placeholders before use)")
            return True
            
    except Exception as e:
        print(f"✗ Config check failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Stats Event Logger Plugin Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Import", test_import()))
    results.append(("Initialization", test_initialization()))
    results.append(("Event Tracking", test_event_tracking()))
    results.append(("Configuration", test_config()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("\nNext steps:")
        print("1. Set up foos-tournament backend (see build plan)")
        print("2. Update league_url, league_apikey, and league_season in config.py")
        print("3. Add 'stats_event_logger' to plugins set in config.py")
        print("4. Restart foos and play a match")
    else:
        print("✗ Some tests failed - check errors above")
        sys.exit(1)

if __name__ == '__main__':
    main()
