#!/bin/bash
#
# test_connectivity.sh - SPtrader External Service Connectivity Tester
#
# Description:
#   Tests connectivity to external services without affecting the database.
#   Used during startup to warn about connection issues and can be run
#   manually to diagnose problems.
#
# Services Tested:
#   - QuestDB: Local database connectivity
#   - Oanda API: Validates API credentials and connectivity
#   - Dukascopy: Checks access to public data feeds
#
# Features:
#   - Non-destructive testing (no data written)
#   - Clear status output with color coding
#   - Detailed error messages for troubleshooting
#   - Can be sourced by other scripts or run standalone
#
# Usage:
#   ./test_connectivity.sh          # Run all tests
#   ./test_connectivity.sh oanda    # Test only Oanda
#   ./test_connectivity.sh dukascopy # Test only Dukascopy
#   ./test_connectivity.sh questdb   # Test only QuestDB
#
# Exit Status:
#   0 - All tests passed
#   1 - One or more tests failed (details in output)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to test QuestDB connectivity
test_questdb() {
    echo -ne "${BLUE}Testing QuestDB connection...${NC} "
    
    # Try a simple query
    response=$(curl -s -G "http://localhost:9000/exec" \
        --data-urlencode "query=SELECT 1" 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$response" | grep -q '"dataset"'; then
        echo -e "${GREEN}✓ Connected${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        echo "  Make sure QuestDB is running on port 9000"
        return 1
    fi
}

# Function to test Oanda API connectivity
test_oanda() {
    echo -ne "${BLUE}Testing Oanda API connection...${NC} "
    
    # Read API key from oanda_feed.py
    API_KEY=$(grep "api_key =" ~/SPtrader/data_feeds/oanda_feed.py 2>/dev/null | \
              sed 's/.*api_key = "\(.*\)"/\1/' | head -1)
    
    if [ -z "$API_KEY" ] || [ "$API_KEY" = "your_api_key_here" ]; then
        echo -e "${YELLOW}⚠ No API key configured${NC}"
        echo "  Update api_key in data_feeds/oanda_feed.py"
        return 1
    fi
    
    # Test API with a simple request (get account summary)
    response=$(curl -s -H "Authorization: Bearer $API_KEY" \
        "https://api-fxpractice.oanda.com/v3/accounts" 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$response" | grep -q '"accounts"'; then
        echo -e "${GREEN}✓ Connected${NC}"
        # Show account ID if available
        account_id=$(echo "$response" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
        [ -n "$account_id" ] && echo "  Account: $account_id"
        return 0
    elif echo "$response" | grep -q "Unauthorized"; then
        echo -e "${RED}✗ Invalid API key${NC}"
        echo "  Check your Oanda API credentials"
        return 1
    else
        echo -e "${RED}✗ Connection failed${NC}"
        echo "  Check internet connection and Oanda API status"
        return 1
    fi
}

# Function to test Dukascopy data feed access
test_dukascopy() {
    echo -ne "${BLUE}Testing Dukascopy data feed...${NC} "
    
    # Test access to Dukascopy public data
    # Try to access the base URL for EURUSD data
    test_url="https://datafeed.dukascopy.com/datafeed/EURUSD/2024/00/01/00h_ticks.bi5"
    
    # Use curl with head request to check accessibility
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --head "$test_url" 2>/dev/null)
    
    if [ "$response_code" = "200" ] || [ "$response_code" = "404" ]; then
        # 200 = file exists, 404 = file doesn't exist but server is accessible
        echo -e "${GREEN}✓ Accessible${NC}"
        echo "  Public data feed is available"
        return 0
    elif [ "$response_code" = "000" ]; then
        echo -e "${RED}✗ No internet connection${NC}"
        echo "  Check your network connectivity"
        return 1
    else
        echo -e "${YELLOW}⚠ Unexpected response (HTTP $response_code)${NC}"
        echo "  Feed may be temporarily unavailable"
        return 1
    fi
}

# Function to run all tests and summarize
run_all_tests() {
    echo -e "${BLUE}=== SPtrader Connectivity Test ===${NC}"
    echo ""
    
    local failed=0
    
    # Test each service
    test_questdb || ((failed++))
    test_oanda || ((failed++))
    test_dukascopy || ((failed++))
    
    # Summary
    echo ""
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✅ All connectivity tests passed!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ $failed service(s) have connectivity issues${NC}"
        echo "  Services will start but may not function fully"
        return 1
    fi
}

# Main execution
# Check if specific service was requested
case "$1" in
    questdb)
        test_questdb
        ;;
    oanda)
        test_oanda
        ;;
    dukascopy)
        test_dukascopy
        ;;
    "")
        run_all_tests
        ;;
    *)
        echo "Usage: $0 [questdb|oanda|dukascopy]"
        exit 1
        ;;
esac