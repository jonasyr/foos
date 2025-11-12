#!/bin/bash
# Quick verification script for stats_event_logger setup
# Run this after completing Parts 1-5 of the build plan

set -e

echo "=========================================="
echo "Stats Event Logger - Setup Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track pass/fail
PASS=0
FAIL=0

# Check 1: Plugin file exists
echo -n "1. Plugin file exists... "
if [ -f "/home/pi/foos-project/foos/plugins/stats_event_logger.py" ]; then
    echo -e "${GREEN}✓${NC}"
    ((PASS++))
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

# Check 2: Plugin is in config
echo -n "2. Plugin enabled in config... "
if grep -q "stats_event_logger" /home/pi/foos-project/foos/config.py; then
    echo -e "${GREEN}✓${NC}"
    ((PASS++))
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

# Check 3: Config has league settings
echo -n "3. League URL configured... "
if grep -q "league_url" /home/pi/foos-project/foos/config.py; then
    URL=$(grep "league_url" /home/pi/foos-project/foos/config.py | cut -d'"' -f2)
    if [[ "$URL" == *"<YOUR-LAN-HOST>"* ]]; then
        echo -e "${YELLOW}⚠ (placeholder - needs update)${NC}"
    else
        echo -e "${GREEN}✓${NC} ($URL)"
        ((PASS++))
    fi
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

echo -n "4. API key configured... "
if grep -q "league_apikey" /home/pi/foos-project/foos/config.py; then
    KEY=$(grep "league_apikey" /home/pi/foos-project/foos/config.py | cut -d'"' -f2)
    if [[ "$KEY" == *"<YOUR-KEY>"* ]]; then
        echo -e "${YELLOW}⚠ (placeholder - needs update)${NC}"
    else
        echo -e "${GREEN}✓${NC} (configured)"
        ((PASS++))
    fi
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

echo -n "5. Season configured... "
if grep -q "league_season" /home/pi/foos-project/foos/config.py; then
    SEASON=$(grep "league_season" /home/pi/foos-project/foos/config.py | cut -d'"' -f2)
    echo -e "${GREEN}✓${NC} ($SEASON)"
    ((PASS++))
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

# Check 6: Test backend connectivity (if configured)
echo ""
echo "Backend Connectivity Test:"
echo "--------------------------"

# Extract config values
URL=$(grep "league_url" /home/pi/foos-project/foos/config.py | cut -d"'" -f2 2>/dev/null || echo "")
KEY=$(grep "league_apikey" /home/pi/foos-project/foos/config.py | cut -d"'" -f2 2>/dev/null || echo "")

if [[ ! -z "$URL" ]] && [[ ! -z "$KEY" ]] && [[ "$URL" != *"<YOUR-LAN-HOST>"* ]] && [[ "$KEY" != *"<YOUR-KEY>"* ]]; then
    echo -n "6. Testing connection to $URL/health... "
    
    RESPONSE=$(curl -s -H "X-API-Key: $KEY" "$URL/health" 2>/dev/null || echo "")
    
    if [[ ! -z "$RESPONSE" ]] && [[ "$RESPONSE" == *"\"ok\":true"* ]]; then
        echo -e "${GREEN}✓${NC}"
        echo "   Response: $RESPONSE"
        ((PASS++))
    else
        echo -e "${RED}✗${NC}"
        echo "   Failed to reach backend. Is foos-tournament running?"
        echo "   Start it with: cd ~/foos-tournament && ruby web_router.rb"
        ((FAIL++))
    fi
else
    echo "6. Backend connectivity... ${YELLOW}⚠ (skipped - update config first)${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASS${NC}"
if [ $FAIL -gt 0 ]; then
    echo -e "Failed: ${RED}$FAIL${NC}"
fi

echo ""
if [ $FAIL -eq 0 ] && [[ "$URL" != *"<YOUR-LAN-HOST>"* ]]; then
    echo -e "${GREEN}✓ Setup complete! Ready to use.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Restart Foos: sudo systemctl restart foos"
    echo "2. Play a match and check logs: journalctl -u foos -f"
    echo "3. View stats via API or (future) Stats menu"
elif [[ "$URL" == *"<YOUR-LAN-HOST>"* ]]; then
    echo -e "${YELLOW}⚠ Configuration needed${NC}"
    echo ""
    echo "Update /home/pi/foos-project/foos/config.py:"
    echo "  - league_url: Replace <YOUR-LAN-HOST> with actual IP"
    echo "  - league_apikey: Replace <YOUR-KEY> with actual key"
    echo ""
    echo "Then run this script again to verify."
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Please fix the issues above and try again."
fi

echo ""
