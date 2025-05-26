#!/bin/bash
#
# start_background.sh - SPtrader Service Startup Script
#
# Description:
#   Starts all SPtrader services in the correct order with health checks.
#   This script ensures dependencies are ready before starting dependent services,
#   handles port conflicts, and provides clear status feedback.
#
# Services started (in order):
#   1. QuestDB (port 9000) - Time-series database
#   2. OHLC Manager - Aggregates tick data into candles
#   3. Oanda Feed - Real-time market data
#   4. FastAPI Backend (port 8000) - REST API
#   5. React Frontend (port 5173) - If configured
#
# Key Features:
#   - Kills existing processes and clears ports before starting
#   - Waits for QuestDB to accept queries before proceeding
#   - Validates FastAPI health endpoint before continuing
#   - Checks package.json validity before starting frontend
#   - Shows detailed error logs if services fail to start
#   - Color-coded output for easy status identification
#
# Health Checks:
#   - QuestDB: Waits up to 30 seconds for port 9000 and query acceptance
#   - FastAPI: Waits up to 20 seconds for /api/health endpoint
#   - Aborts if critical services (QuestDB) fail to start
#
# Error Handling:
#   - Shows last 10 lines of logs if FastAPI fails
#   - Validates package.json before npm install
#   - Continues even if optional services fail
#
# Usage:
#   ./start_background.sh    # Direct execution
#   sptrader start          # Via CLI wrapper
#
# Logs:
#   All services log to ~/SPtrader/logs/
#   - questdb.log, fastapi.log, oanda_feed.log, etc.

SPTRADER_HOME="$HOME/SPtrader"
LOG_DIR="$SPTRADER_HOME/logs"
RUNTIME_LOG_DIR="$LOG_DIR/runtime"
STATUS_LOG_DIR="$LOG_DIR/status"
API_DIR="$SPTRADER_HOME/api"
FRONTEND_DIR="$SPTRADER_HOME/frontend"

# Ensure log directories exist
mkdir -p "$RUNTIME_LOG_DIR" "$STATUS_LOG_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

mkdir -p "$LOG_DIR"

echo "=== Starting SPtrader Services ==="

# Function to check if process is running
check_process() {
    pgrep -f "$1" > /dev/null
    return $?
}

# Function to kill process using a port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}Killing process on port $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
}

# Clean up any existing processes
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -9 -f questdb
pkill -9 -f "uvicorn.*main:app"
pkill -9 -f "npm.*dev"
pkill -9 -f oanda_feed
pkill -9 -f ohlc_manager
pkill -9 -f dukascopy_importer

# Also clean up any processes holding our ports
kill_port 9000  # QuestDB
kill_port 8000  # FastAPI
kill_port 5173  # React dev server

sleep 3

# Start QuestDB
echo -e "${YELLOW}Starting QuestDB...${NC}"
cd ~/questdb-8.3.1-rt-linux-x86-64
./bin/questdb.sh start > "$RUNTIME_LOG_DIR/questdb.log" 2>&1

# Wait for QuestDB to be ready
echo -ne "${YELLOW}Waiting for QuestDB to be ready...${NC}"
QUESTDB_READY=false
for i in {1..30}; do
    # Check if port 9000 is listening
    if netstat -tln 2>/dev/null | grep -q ":9000 "; then
        # Try a simple query to verify it's accepting connections
        if curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT 1" >/dev/null 2>&1; then
            QUESTDB_READY=true
            break
        fi
    fi
    echo -n "."
    sleep 1
done

if [ "$QUESTDB_READY" = true ]; then
    echo -e " ${GREEN}✓ Ready${NC}"
else
    echo -e " ${RED}✗ Failed${NC}"
    echo -e "${RED}QuestDB is not responding. Check logs at: $RUNTIME_LOG_DIR/questdb.log${NC}"
    echo -e "${RED}Aborting startup.${NC}"
    exit 1
fi

# Run connectivity tests (non-blocking)
echo ""
echo -e "${YELLOW}Running connectivity tests...${NC}"
"$SPTRADER_HOME/tools/test_connectivity.sh" > "$STATUS_LOG_DIR/connectivity_test.log" 2>&1

# Show brief results without blocking startup
if grep -q "All connectivity tests passed" "$LOG_DIR/connectivity_test.log"; then
    echo -e "${GREEN}✓ External services connectivity OK${NC}"
else
    echo -e "${YELLOW}⚠ Some external services may not be accessible${NC}"
    echo -e "${YELLOW}  Check $STATUS_LOG_DIR/connectivity_test.log for details${NC}"
    echo -e "${YELLOW}  Services will start but may have limited functionality${NC}"
fi
echo ""

# Start OHLC manager (handles data aggregation)
echo -e "${YELLOW}Starting OHLC manager...${NC}"
cd ~/SPtrader/scripts  
echo "y" | nohup python3 ohlc_manager.py > "$RUNTIME_LOG_DIR/ohlc_manager.log" 2>&1 &
sleep 2

if check_process "ohlc_manager"; then
    echo -e "${GREEN}✓ OHLC manager started${NC}"
else
    echo -e "${RED}✗ OHLC manager failed to start${NC}"
fi

# Start live data feed (Oanda)
echo -e "${YELLOW}Starting Oanda live feed...${NC}"
cd ~/SPtrader/data_feeds
echo "y" | nohup python3 oanda_feed.py > "$RUNTIME_LOG_DIR/oanda_feed.log" 2>&1 &
sleep 2

if check_process "oanda_feed"; then
    echo -e "${GREEN}✓ Oanda feed started${NC}"
else
    echo -e "${RED}✗ Oanda feed failed to start${NC}"
fi

# Start FastAPI backend
echo -e "${YELLOW}Starting FastAPI backend...${NC}"
cd "$API_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$RUNTIME_LOG_DIR/fastapi.log" 2>&1 &
deactivate

# Wait for FastAPI to be ready
echo -ne "${YELLOW}Waiting for FastAPI backend...${NC}"
API_READY=false
for i in {1..20}; do
    if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
        API_READY=true
        break
    fi
    echo -n "."
    sleep 1
done

if [ "$API_READY" = true ]; then
    echo -e " ${GREEN}✓ Ready${NC}"
else
    echo -e " ${RED}✗ Failed${NC}"
    echo -e "${RED}FastAPI backend failed to start. Check logs at: $RUNTIME_LOG_DIR/fastapi.log${NC}"
    echo -e "${YELLOW}Last 10 lines of log:${NC}"
    tail -10 "$RUNTIME_LOG_DIR/fastapi.log"
fi

# Start React frontend (if package.json exists)
if [ -f "$FRONTEND_DIR/package.json" ]; then
    # Validate package.json is not empty
    if [ ! -s "$FRONTEND_DIR/package.json" ] || ! python3 -m json.tool "$FRONTEND_DIR/package.json" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Frontend package.json is empty or invalid${NC}"
        echo -e "${YELLOW}  Skipping frontend startup${NC}"
    else
        echo -e "${YELLOW}Starting React frontend...${NC}"
        cd "$FRONTEND_DIR"
        
        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi
        
        nohup npm run dev > "$RUNTIME_LOG_DIR/frontend.log" 2>&1 &
        sleep 5
        
        if check_process "npm.*dev"; then
            echo -e "${GREEN}✓ React frontend started${NC}"
        else
            echo -e "${RED}✗ React frontend failed to start${NC}"
            echo -e "${YELLOW}Check logs at: $RUNTIME_LOG_DIR/frontend.log${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠ Frontend not configured (no package.json found)${NC}"
fi

# Summary
echo ""
echo "==================================="
echo -e "${GREEN}✅ SPtrader Services Started!${NC}"
echo "==================================="
echo ""
echo "📊 Services:"
echo "  • QuestDB Console: http://localhost:9000"
echo "  • FastAPI Backend: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • React Frontend: http://localhost:5173 (if configured)"
echo ""
echo "📁 Logs: $RUNTIME_LOG_DIR/ (services), $STATUS_LOG_DIR/ (status)"
echo ""
echo "🔍 Useful Commands:"
echo "  • Monitor all logs: tail -f $RUNTIME_LOG_DIR/*.log"
echo "  • Check services: ./tools/check_services.sh"
echo "  • Stop all: ./stop_all.sh"
echo "  • API test: curl http://localhost:8000/api/health"
echo ""