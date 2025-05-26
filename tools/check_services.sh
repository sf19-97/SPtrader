#!/bin/bash
#
# check_services.sh - SPtrader Service Status Checker
# 
# Description:
#   Comprehensive health check for all SPtrader services. This script checks:
#   - Process status for each service (QuestDB, Go API, React, data feeds)
#   - Port availability (ensures services are listening on expected ports)
#   - API health endpoint connectivity
#   - Cache statistics and performance metrics
#   - Database connectivity and data counts
#   - Provides color-coded output for easy status identification
#
# Usage:
#   ./check_services.sh
#   sptrader status       # When using the CLI wrapper
#
# Output includes:
#   - Service status with port verification
#   - API health and database connection status
#   - Cache hit rates and usage statistics
#   - Data counts for both v1 (Oanda) and v2 (Dukascopy) tables
#   - Quick links to all service URLs
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more services are not running (script continues)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=== SPtrader Service Status ==="
echo ""

# Function to check if service is running
check_service() {
    local name=$1
    local pattern=$2
    local port=$3
    
    if pgrep -f "$pattern" > /dev/null 2>&1; then
        if [ -n "$port" ]; then
            # Also check if port is listening
            if netstat -tln 2>/dev/null | grep -q ":$port "; then
                echo -e "${GREEN}✅ $name${NC} (port $port)"
            else
                echo -e "${YELLOW}⚠  $name${NC} (process running but port $port not listening)"
            fi
        else
            echo -e "${GREEN}✅ $name${NC}"
        fi
        return 0
    else
        echo -e "${RED}❌ $name${NC}"
        return 1
    fi
}

# Check core services
echo -e "${BLUE}Core Services:${NC}"
check_service "QuestDB" "questdb.*ServerMain" "9000"
check_service "Go API Backend" "uvicorn.*main:app" "8000"
check_service "React Frontend" "npm.*dev" "5173"

echo ""
echo -e "${BLUE}Data Feeds:${NC}"
check_service "Oanda Live Feed" "oanda_feed.py"
check_service "OHLC Manager" "ohlc_manager.py"
check_service "Dukascopy Importer" "dukascopy_importer.py"

# API Health Check
echo ""
echo -e "${BLUE}API Health Check:${NC}"
API_HEALTH=$(curl -s http://localhost:8080/api/v1/health 2>/dev/null)
if [ $? -eq 0 ] && echo "$API_HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ API is healthy${NC}"
    DB_STATUS=$(echo "$API_HEALTH" | grep -o '"database":"[^"]*' | cut -d'"' -f4)
    echo "   Database: $DB_STATUS"
else
    echo -e "${RED}❌ API is not responding${NC}"
fi

# Cache Statistics
echo ""
echo -e "${BLUE}Cache Statistics:${NC}"
CACHE_STATS=$(curl -s http://localhost:8000/api/stats 2>/dev/null)
if [ $? -eq 0 ]; then
    HIT_RATE=$(echo "$CACHE_STATS" | grep -o '"hit_rate":"[^"]*' | cut -d'"' -f4)
    CACHE_SIZE=$(echo "$CACHE_STATS" | grep -o '"size":[0-9]*' | head -1 | cut -d':' -f2)
    MAX_SIZE=$(echo "$CACHE_STATS" | grep -o '"max_size":[0-9]*' | cut -d':' -f2)
    echo "   Hit Rate: $HIT_RATE"
    echo "   Cache Usage: $CACHE_SIZE/$MAX_SIZE"
else
    echo "   Unable to fetch cache stats"
fi

# Database Statistics
echo ""
echo -e "${BLUE}Database Statistics:${NC}"

# Check for v2 data (multi-symbol tables)
V2_COUNT=$(curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT count(*) FROM ohlc_5m_v2" 2>/dev/null | grep -o '"dataset":\[\[[0-9]*' | grep -o '[0-9]*' | tail -1)
V2_LATEST=$(curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT max(timestamp) FROM ohlc_5m_v2" 2>/dev/null | grep -o '"dataset":\[\["[^"]*' | sed 's/.*\["//')

# Check for v1 data (Oanda)
V1_COUNT=$(curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT count(*) FROM eurusd_5m_oanda" 2>/dev/null | grep -o '"dataset":\[\[[0-9]*' | grep -o '[0-9]*' | tail -1)
V1_LATEST=$(curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT max(timestamp) FROM eurusd_5m_oanda" 2>/dev/null | grep -o '"dataset":\[\["[^"]*' | sed 's/.*\["//')

if [ -n "$V2_COUNT" ] || [ -n "$V1_COUNT" ]; then
    if [ -n "$V2_COUNT" ]; then
        echo "   V2 Data (Dukascopy): $V2_COUNT records"
        echo "   Latest: $V2_LATEST"
    fi
    if [ -n "$V1_COUNT" ]; then
        echo "   V1 Data (Oanda): $V1_COUNT records"
        echo "   Latest: $V1_LATEST"
    fi
else
    echo "   No data available or QuestDB not responding"
fi

# URLs Summary
echo ""
echo -e "${BLUE}Service URLs:${NC}"
echo "   📊 QuestDB Console: http://localhost:9000"
echo "   🚀 Go API Backend: http://localhost:8000"
echo "   📖 API Documentation: http://localhost:8000/docs"
echo "   ⚛️  React Frontend: http://localhost:5173"

# Process Details
echo ""
echo -e "${BLUE}Process Details:${NC}"
echo "   To view logs: tail -f ~/SPtrader/logs/*.log"
echo "   To stop all: ~/SPtrader/stop_all.sh"
echo "   To monitor: ~/SPtrader/tools/monitor.sh"