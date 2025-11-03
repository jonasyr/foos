#!/usr/bin/env python3
"""Test the buttons.py press() function fix."""

import sys
sys.path.insert(0, '/home/pi/foos')

from plugins.buttons import down

print("Testing buttons.py press() function")
print("=" * 60)

# Test 1: No long parameter (should register both short and long)
print("\n1. down(['btn'], ('action', {}))  # No long parameter")
result1 = down(['btn'], ('action', {}))
print(f"   Keys registered: {list(result1.keys())}")
short_count = sum(1 for k in result1.keys() if k[2] == 'short')
long_count = sum(1 for k in result1.keys() if k[2] == 'long')
print(f"   Short: {short_count}, Long: {long_count}")
if short_count == 1 and long_count == 1:
    print("   ✅ PASS: Both short and long registered")
else:
    print("   ❌ FAIL: Expected 1 short and 1 long")

# Test 2: long=None (should register ONLY short)
print("\n2. down(['btn'], ('action', {}), long=None)  # Explicit None")
result2 = down(['btn'], ('action', {}), long=None)
print(f"   Keys registered: {list(result2.keys())}")
short_count = sum(1 for k in result2.keys() if k[2] == 'short')
long_count = sum(1 for k in result2.keys() if k[2] == 'long')
print(f"   Short: {short_count}, Long: {long_count}")
if short_count == 1 and long_count == 0:
    print("   ✅ PASS: Only short registered")
else:
    print("   ❌ FAIL: Expected 1 short and 0 long")

# Test 3: long=different_action (should register both with different actions)
print("\n3. down(['btn'], ('action1', {}), long=('action2', {}))  # Different long")
result3 = down(['btn'], ('action1', {}), long=('action2', {}))
print(f"   Keys registered: {list(result3.keys())}")
short_count = sum(1 for k in result3.keys() if k[2] == 'short')
long_count = sum(1 for k in result3.keys() if k[2] == 'long')
print(f"   Short: {short_count}, Long: {long_count}")
if short_count == 1 and long_count == 1:
    print("   ✅ PASS: Both short and long registered")
    # Check actions are different
    short_action = [v[0] for k, v in result3.items() if k[2] == 'short'][0]
    long_action = [v[0] for k, v in result3.items() if k[2] == 'long'][0]
    if short_action[0] == 'action1' and long_action[0] == 'action2':
        print("   ✅ PASS: Different actions registered")
    else:
        print("   ❌ FAIL: Actions not different")
else:
    print("   ❌ FAIL: Expected 1 short and 1 long")

print("\n" + "=" * 60)
print("✅ Test complete!")
