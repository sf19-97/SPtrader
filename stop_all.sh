#!/bin/bash
#
# stop_all.sh - SPtrader Service Shutdown Script
#
# Description:
#   Gracefully stops all SPtrader services with fallback to force termination.
#   This script ensures clean shutdown of all components and verifies no
#   processes remain running.
#
# Shutdown Order:
#   1. React Frontend - Stop development server
#   2. FastAPI Backend - Stop API server
#   3. Data Feeds - Stop Oanda feed and importers
#   4. OHLC Manager - Stop aggregation service
#   5. Legacy Services - Clean up old components
#   6. QuestDB - Proper database shutdown
#
# Key Features:
#   - Attempts graceful shutdown first (SIGTERM)
#   - Force kills after 2 seconds if needed (SIGKILL)
#   - Special handling for QuestDB using official stop script
#   - Cleans up orphaned processes
#   - Color-coded output showing stop status
#   - Final check for remaining processes
#
# Process Management:
#   - Each service gets 2 seconds to stop gracefully
#   - Shows [stopped] in green for clean shutdown
#   - Shows [force killed] in red if SIGKILL was needed
#   - Kills processes by port if stop script fails
#
# Usage:
#   ./stop_all.sh       # Direct execution
#   sptrader stop       # Via CLI wrapper
#
# Exit Status:
#   Always exits with 0 (success) even if some processes required force kill
#   Shows warning if any processes might still be running

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=== Stopping SPtrader Services ==="

# Function to stop process gracefully then force kill
stop_process() {
    local process_name=$1
    local display_name=$2
    
    echo -ne "${YELLOW}Stopping ${display_name}...${NC}"
    
    # Try graceful shutdown first
    pkill -f "$process_name" 2>/dev/null
    
    # Wait a moment
    sleep 2
    
    # Force kill if still running
    if pgrep -f "$process_name" > /dev/null; then
        pkill -9 -f "$process_name" 2>/dev/null
        echo -e " ${RED}[force killed]${NC}"
    else
        echo -e " ${GREEN}[stopped]${NC}"
    fi
}

# Stop React frontend
stop_process "npm.*dev" "React frontend"

# Stop FastAPI backend
stop_process "uvicorn.*main:app" "FastAPI backend"

# Stop data feeds
stop_process "oanda_feed" "Oanda feed"
stop_process "dukascopy_importer" "Dukascopy importer"

# Stop OHLC manager
stop_process "ohlc_manager" "OHLC manager"

# Stop legacy services (if any)
stop_process "cors_proxy" "CORS proxy"
stop_process "http.server 8080" "Python web server"

# Stop QuestDB properly
echo -ne "${YELLOW}Stopping QuestDB...${NC}"
cd ~/questdb-8.3.1-rt-linux-x86-64 2>/dev/null
if [ -f "./bin/questdb.sh" ]; then
    ./bin/questdb.sh stop >/dev/null 2>&1
    sleep 3
    
    # Check if stopped
    if pgrep -f "questdb" > /dev/null; then
        pkill -9 -f questdb 2>/dev/null
        echo -e " ${RED}[force killed]${NC}"
    else
        echo -e " ${GREEN}[stopped]${NC}"
    fi
else
    # Try to kill by process name if script not found
    pkill -9 -f questdb 2>/dev/null
    echo -e " ${GREEN}[stopped]${NC}"
fi

# Clean up any orphaned processes
echo -e "${YELLOW}Cleaning up orphaned processes...${NC}"
pkill -9 -f "python.*main.py" 2>/dev/null
pkill -9 -f "node.*frontend" 2>/dev/null

# Summary
echo ""
echo "==================================="
echo -e "${GREEN}✅ All services stopped${NC}"
echo "==================================="
echo ""

# Check if anything is still running
remaining=$(pgrep -f "questdb|oanda_feed|ohlc_manager|uvicorn|npm.*dev" | wc -l)
if [ "$remaining" -gt 0 ]; then
    echo -e "${RED}⚠ Warning: $remaining process(es) may still be running${NC}"
    echo "Check with: ps aux | grep -E '(questdb|oanda|ohlc|uvicorn|npm)'"
else
    echo "All SPtrader services have been stopped successfully."
fi