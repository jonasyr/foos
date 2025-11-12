#!/usr/bin/env python3
"""
Integration Test for Stats Event Logger

This script verifies:
1. foos-tournament is accessible
2. API authentication works
3. Required endpoints exist
4. stats_event_logger plugin is properly configured
"""

import sys
import json
import urllib.request
import urllib.error

# Test configuration
TOURNAMENT_URL = 'http://localhost:4567'  # Update with your host
API_KEY = 'change-me-supersecret'  # Update with your API key

def test_connection():
    """Test basic connectivity to foos-tournament"""
    print("🔍 Testing connection to foos-tournament...")
    try:
        response = urllib.request.urlopen(f"{TOURNAMENT_URL}/", timeout=5)
        print("✅ foos-tournament is accessible")
        return True
    except urllib.error.URLError as e:
        print(f"❌ Cannot connect to foos-tournament: {e}")
        print(f"   Make sure it's running on {TOURNAMENT_URL}")
        return False

def test_api_players():
    """Test existing API endpoint (no auth required)"""
    print("\n🔍 Testing /api/v1/players endpoint...")
    try:
        req = urllib.request.Request(f"{TOURNAMENT_URL}/api/v1/players")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            print(f"✅ Players API works: {len(data)} players found")
            if data:
                print(f"   Sample: {list(data.values())[0]}")
            return True
    except urllib.error.URLError as e:
        print(f"❌ Players API failed: {e}")
        return False

def test_api_seasons():
    """Test seasons endpoint"""
    print("\n🔍 Testing /api/v1/seasons endpoint...")
    try:
        req = urllib.request.Request(f"{TOURNAMENT_URL}/api/v1/seasons")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            print(f"✅ Seasons API works: {len(data)} seasons found")
            if data:
                print(f"   Sample: {data[0]['name']}")
            return True
    except urllib.error.URLError as e:
        print(f"❌ Seasons API failed: {e}")
        return False

def test_stats_api_exists():
    """Test if extended stats API endpoints exist (from build plan)"""
    print("\n🔍 Checking for extended stats API...")
    print("   (This requires Parts 2-4 of the build plan)")
    
    # Try to POST to a non-existent match (should get 401/403 or 404)
    try:
        url = f"{TOURNAMENT_URL}/api/matches/999999/goals"
        headers = {
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        }
        body = json.dumps({'events': []}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            print("✅ Stats API endpoints exist!")
            return True
            
    except urllib.error.HTTPError as e:
        if e.code == 401 or e.code == 403:
            print("⚠️  Stats API exists but authentication failed")
            print(f"   Check API key: {API_KEY}")
            return False
        elif e.code == 404:
            print("❌ Stats API not implemented yet")
            print("   Complete Parts 2-4 of build plan to enable stats")
            return False
        else:
            print(f"⚠️  Unexpected response: {e.code}")
            return False
            
    except urllib.error.URLError as e:
        print(f"❌ Network error: {e}")
        return False

def test_plugin_import():
    """Test if stats_event_logger plugin can be imported"""
    print("\n🔍 Testing stats_event_logger plugin import...")
    try:
        sys.path.insert(0, '/home/pi/foos-project/foos')
        from plugins import stats_event_logger
        print("✅ Plugin imports successfully")
        
        # Check for required methods
        required = ['on_match_start', 'on_goal', 'on_match_end', 'on_match_cancel']
        for method in required:
            if not hasattr(stats_event_logger.Plugin, method):
                print(f"❌ Missing method: {method}")
                return False
        print("✅ All required methods present")
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import plugin: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking plugin: {e}")
        return False

def check_config():
    """Check foos config.py settings"""
    print("\n🔍 Checking foos config.py...")
    try:
        sys.path.insert(0, '/home/pi/foos-project/foos')
        import config
        
        # Check required settings
        checks = [
            ('league_url', 'Tournament URL'),
            ('league_apikey', 'API key'),
        ]
        
        all_good = True
        for attr, name in checks:
            if hasattr(config, attr):
                value = getattr(config, attr)
                if '<YOUR' in str(value) or not value:
                    print(f"⚠️  {name} needs configuration: {attr} = '{value}'")
                    all_good = False
                else:
                    print(f"✅ {name} configured")
            else:
                print(f"❌ Missing setting: {attr}")
                all_good = False
        
        # Check plugin is enabled
        if hasattr(config, 'plugins'):
            if 'stats_event_logger' in config.plugins:
                print("✅ stats_event_logger plugin enabled")
            else:
                print("⚠️  stats_event_logger not in plugins list")
                all_good = False
        
        # Check stats API flag
        if hasattr(config, 'league_stats_api'):
            if config.league_stats_api:
                print("✅ league_stats_api enabled (will attempt uploads)")
            else:
                print("ℹ️  league_stats_api disabled (tracking only, no upload)")
        else:
            print("ℹ️  league_stats_api not set (defaults to False)")
            
        return all_good
        
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def main():
    print("=" * 70)
    print("Stats Event Logger Integration Test")
    print("=" * 70)
    
    results = {
        'Connection': test_connection(),
        'Players API': test_api_players(),
        'Seasons API': test_api_seasons(),
        'Stats API': test_stats_api_exists(),
        'Plugin Import': test_plugin_import(),
        'Config': check_config(),
    }
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {test}")
    
    print("\n" + "=" * 70)
    
    # Overall status
    if all(results.values()):
        print("🎉 All tests passed! System is ready for stats logging.")
        return 0
    elif results['Connection'] and results['Plugin Import']:
        print("⚠️  Basic functionality ready, but stats API not fully configured.")
        print("   You can use the plugin in tracking-only mode (league_stats_api=False)")
        print("   Complete build plan Parts 2-4 to enable full stats upload.")
        return 1
    else:
        print("❌ Critical issues found. Please fix errors above.")
        return 2

if __name__ == '__main__':
    sys.exit(main())
