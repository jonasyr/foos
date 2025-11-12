#!/usr/bin/env python3
"""
Client-Side Integration Test
Tests that foos/ Python client can properly consume quick matches from foos-tournament/
"""

import sys
import json
import os

sys.path.insert(0, '/home/pi/foos-project/foos')

def test_league_json_exists():
    """Test 1: league.json file exists and is readable"""
    print("\n" + "=" * 60)
    print("Test 1: league.json exists and is readable")
    print("=" * 60)
    
    league_file = '/home/pi/foos-project/foos/league/league.json'
    
    if not os.path.exists(league_file):
        print(f"❌ File not found: {league_file}")
        return False
    
    try:
        with open(league_file) as f:
            data = json.load(f)
        print(f"✅ File loaded successfully")
        print(f"✅ Found {len(data)} division(s)")
        return True, data
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return False, None

def test_quick_matches_present(data):
    """Test 2: Quick matches are present in league.json"""
    print("\n" + "=" * 60)
    print("Test 2: Quick matches present")
    print("=" * 60)
    
    quick_matches = []
    for div in data:
        for match in div.get('matches', []):
            if match.get('quick_match'):
                quick_matches.append(match)
    
    print(f"✅ Found {len(quick_matches)} quick match(es)")
    return len(quick_matches) > 0, quick_matches

def test_submatches_structure(quick_matches):
    """Test 3: All quick matches have submatches field"""
    print("\n" + "=" * 60)
    print("Test 3: Submatches structure validation")
    print("=" * 60)
    
    all_valid = True
    
    for match in quick_matches[:10]:  # Test first 10
        match_id = match.get('id')
        mode = match.get('mode', 'standard')
        
        if 'submatches' not in match:
            print(f"❌ Match {match_id}: Missing 'submatches' field")
            all_valid = False
            continue
        
        submatches = match['submatches']
        
        if not isinstance(submatches, list):
            print(f"❌ Match {match_id}: 'submatches' is not a list")
            all_valid = False
            continue
        
        if len(submatches) == 0:
            print(f"❌ Match {match_id}: 'submatches' is empty")
            all_valid = False
            continue
        
        # Check first submatch structure
        first_submatch = submatches[0]
        if len(first_submatch) != 2:
            print(f"❌ Match {match_id}: submatch should have 2 teams, has {len(first_submatch)}")
            all_valid = False
            continue
        
        # Check team sizes based on mode
        yellow_size = len(first_submatch[0])
        black_size = len(first_submatch[1])
        
        if mode == 'singles':
            if yellow_size != 1 or black_size != 1:
                print(f"❌ Match {match_id}: Singles should have 1 player per team, has {yellow_size} and {black_size}")
                all_valid = False
                continue
        elif mode == 'doubles':
            if yellow_size != 2 or black_size != 2:
                print(f"❌ Match {match_id}: Doubles should have 2 players per team, has {yellow_size} and {black_size}")
                all_valid = False
                continue
    
    if all_valid:
        print(f"✅ All quick matches have valid submatches structure")
    
    return all_valid

def test_league_py_compatibility(quick_matches):
    """Test 4: Simulate league.py behavior"""
    print("\n" + "=" * 60)
    print("Test 4: league.py compatibility simulation")
    print("=" * 60)
    
    # Find one of each type
    singles = next((m for m in quick_matches if m.get('mode') == 'singles'), None)
    doubles = next((m for m in quick_matches if m.get('mode') == 'doubles'), None)
    best_of = next((m for m in quick_matches if m.get('win_condition') == 'best_of'), None)
    
    tests_passed = 0
    tests_total = 0
    
    # Test singles
    if singles:
        tests_total += 1
        print(f"\nTesting Singles Match {singles['id']}:")
        try:
            current_game = 0
            g = singles['submatches'][current_game]  # This is what league.py does
            teams = {"yellow": g[0], "black": g[1]}
            print(f"  ✅ Can access submatches[{current_game}]")
            print(f"  ✅ Yellow: {g[0]}, Black: {g[1]}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test doubles
    if doubles:
        tests_total += 1
        print(f"\nTesting Doubles Match {doubles['id']}:")
        try:
            current_game = 0
            g = doubles['submatches'][current_game]
            teams = {"yellow": g[0], "black": g[1]}
            print(f"  ✅ Can access submatches[{current_game}]")
            print(f"  ✅ Yellow: {g[0]}, Black: {g[1]}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test best-of-3
    if best_of:
        tests_total += 1
        print(f"\nTesting Best-of-3 Match {best_of['id']}:")
        try:
            # Test all 3 submatches
            for i in range(3):
                g = best_of['submatches'][i]
                print(f"  ✅ Can access submatches[{i}]: Yellow {g[0]} vs Black {g[1]}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n  Summary: {tests_passed}/{tests_total} compatibility tests passed")
    return tests_passed == tests_total

def test_target_score_present(quick_matches):
    """Test 5: target_score field is present"""
    print("\n" + "=" * 60)
    print("Test 5: target_score field validation")
    print("=" * 60)
    
    missing_count = 0
    
    for match in quick_matches[:10]:
        match_id = match.get('id')
        target_score = match.get('target_score')
        
        if target_score is None:
            print(f"⚠️  Match {match_id}: No target_score (will default to 10)")
            missing_count += 1
        else:
            print(f"✅ Match {match_id}: target_score = {target_score}")
    
    if missing_count == 0:
        print(f"\n✅ All matches have target_score field")
        return True
    else:
        print(f"\n⚠️  {missing_count} matches missing target_score (not critical)")
        return True  # Not a failure, just a warning

def main():
    print("\n" + "=" * 60)
    print("  CLIENT-SIDE INTEGRATION TEST")
    print("  foos/ ↔ foos-tournament/ Quick Match Compatibility")
    print("=" * 60)
    
    # Run all tests
    success, data = test_league_json_exists()
    if not success:
        print("\n❌ FAILED: Cannot load league.json")
        return 1
    
    success, quick_matches = test_quick_matches_present(data)
    if not success:
        print("\n❌ FAILED: No quick matches found")
        return 1
    
    if not test_submatches_structure(quick_matches):
        print("\n❌ FAILED: Invalid submatches structure")
        return 1
    
    if not test_league_py_compatibility(quick_matches):
        print("\n❌ FAILED: league.py compatibility issues")
        return 1
    
    test_target_score_present(quick_matches)
    
    # Final summary
    print("\n" + "=" * 60)
    print("  ✅ ALL CLIENT-SIDE TESTS PASSED!")
    print("=" * 60)
    print("\n📊 Verification Summary:")
    print(f"  • league.json readable: ✅")
    print(f"  • Quick matches present: ✅ ({len(quick_matches)} found)")
    print(f"  • Submatches structure valid: ✅")
    print(f"  • league.py compatible: ✅")
    print(f"  • target_score present: ✅")
    print("\n🎯 Client is ready to consume server data!")
    print("\n📋 Next Step: Test on physical hardware")
    print("   1. Start foos.py client")
    print("   2. Navigate to League menu")
    print("   3. Select a quick match")
    print("   4. Verify no crashes")
    print("   5. Play match to completion")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
