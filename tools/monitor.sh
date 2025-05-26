#!/bin/bash
#
# monitor.sh - SPtrader Real-Time Monitoring Dashboard
#
# Description:
#   Interactive real-time monitoring dashboard for SPtrader. Provides live updates
#   of system status, performance metrics, and market data. Auto-refreshes every
#   5 seconds with interactive commands for system control.
#
# Features:
#   - Service status with memory usage for each component
#   - API statistics (requests, cache hit rate, database pool)
#   - Latest market prices from Oanda feed
#   - Database activity metrics
#   - System resource usage (CPU, memory, disk)
#   - Interactive commands for quick actions
#
# Interactive Commands:
#   L - View logs (tail -f all log files)
#   S - Stop all services
#   R - Restart all services
#   Q - Quit monitor
#
# Display includes:
#   - Color-coded service status (green=running, red=stopped)
#   - Memory usage per service in MB
#   - API performance metrics and cache statistics
#   - Live market prices extracted from feed logs
#   - Database record counts for recent activity
#   - System CPU, memory, and disk usage
#
# Usage:
#   ./monitor.sh         # Direct execution
#   sptrader monitor     # Via CLI wrapper
#
# Requirements:
#   - curl for API calls
#   - netstat for port checking
#   - Standard Unix tools (ps, top, free, df)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

LOG_DIR="$HOME/SPtrader/logs"
RUNTIME_LOG_DIR="$LOG_DIR/runtime"
STATUS_LOG_DIR="$LOG_DIR/status"

echo -e "${BLUE}=== SPtrader Real-Time Monitor ===${NC}"
echo "Press Ctrl+C to exit"
echo ""

# Function to format numbers with commas
format_number() {
    printf "%'d" $1
}

# Function to get process memory usage
get_memory() {
    local pattern=$1
    local pid=$(pgrep -f "$pattern" | head -1)
    if [ -n "$pid" ]; then
        ps -p $pid -o rss= | awk '{printf "%.1f MB", $1/1024}'
    else
        echo "N/A"
    fi
}

# Main monitoring loop
while true; do
    clear
    echo -e "${BLUE}=== SPtrader Status - $(date) ===${NC}"
    echo ""
    
    # Service Status with Memory Usage
    echo -e "${CYAN}Services:${NC}"
    printf "%-25s %-10s %s\n" "Service" "Status" "Memory"
    printf "%-25s %-10s %s\n" "-------" "------" "------"
    
    # Check each service
    if pgrep -f "questdb.*ServerMain" > /dev/null; then
        printf "%-25s ${GREEN}%-10s${NC} %s\n" "QuestDB" "Running" "$(get_memory 'questdb.*ServerMain')"
    else
        printf "%-25s ${RED}%-10s${NC} %s\n" "QuestDB" "Stopped" "-"
    fi
    
    if pgrep -f "sptrader-api" > /dev/null; then
        printf "%-25s ${GREEN}%-10s${NC} %s\n" "FastAPI Backend" "Running" "$(get_memory 'uvicorn.*main:app')"
    else
        printf "%-25s ${RED}%-10s${NC} %s\n" "FastAPI Backend" "Stopped" "-"
    fi
    
    if pgrep -f "npm.*dev" > /dev/null; then
        printf "%-25s ${GREEN}%-10s${NC} %s\n" "React Frontend" "Running" "$(get_memory 'npm.*dev')"
    else
        printf "%-25s ${RED}%-10s${NC} %s\n" "React Frontend" "Stopped" "-"
    fi
    
    if pgrep -f "oanda_feed.py" > /dev/null; then
        printf "%-25s ${GREEN}%-10s${NC} %s\n" "Oanda Feed" "Running" "$(get_memory 'oanda_feed.py')"
    else
        printf "%-25s ${RED}%-10s${NC} %s\n" "Oanda Feed" "Stopped" "-"
    fi
    
    if pgrep -f "ohlc_manager.py" > /dev/null; then
        printf "%-25s ${GREEN}%-10s${NC} %s\n" "OHLC Manager" "Running" "$(get_memory 'ohlc_manager.py')"
    else
        printf "%-25s ${RED}%-10s${NC} %s\n" "OHLC Manager" "Stopped" "-"
    fi
    
    # API Statistics
    echo ""
    echo -e "${CYAN}API Statistics:${NC}"
    API_STATS=$(curl -s http://localhost:8080/api/v1/stats 2>/dev/null)
    if [ $? -eq 0 ]; then
        REQUESTS=$(echo "$API_STATS" | grep -o '"total_requests":[0-9]*' | cut -d':' -f2)
        HIT_RATE=$(echo "$API_STATS" | grep -o '"hit_rate":"[^"]*' | cut -d'"' -f4)
        CACHE_SIZE=$(echo "$API_STATS" | grep -o '"size":[0-9]*' | head -1 | cut -d':' -f2)
        DB_FREE=$(echo "$API_STATS" | grep -o '"pool_free":[0-9]*' | cut -d':' -f2)
        DB_SIZE=$(echo "$API_STATS" | grep -o '"pool_size":[0-9]*' | cut -d':' -f2)
        
        printf "  %-20s: %s\n" "Total Requests" "$(format_number $REQUESTS)"
        printf "  %-20s: %s\n" "Cache Hit Rate" "$HIT_RATE"
        printf "  %-20s: %d items\n" "Cache Size" "$CACHE_SIZE"
        printf "  %-20s: %d/%d connections\n" "DB Pool" "$DB_FREE" "$DB_SIZE"
    else
        echo "  API not responding"
    fi
    
    # Latest Market Data
    echo ""
    echo -e "${CYAN}Latest Market Prices:${NC}"
    if [ -f "$RUNTIME_LOG_DIR/oanda_feed.log" ]; then
        # Extract latest prices from log
        tail -20 "$RUNTIME_LOG_DIR/oanda_feed.log" | grep -E "session:|bid:|ask:" | tail -5 | while read line; do
            if echo "$line" | grep -q "session:"; then
                SYMBOL=$(echo "$line" | grep -o "session: [A-Z]*" | cut -d' ' -f2)
                echo -e "  ${YELLOW}$SYMBOL${NC}:"
            elif echo "$line" | grep -q "bid:"; then
                BID=$(echo "$line" | grep -o "bid: [0-9.]*" | cut -d' ' -f2)
                ASK=$(echo "$line" | grep -o "ask: [0-9.]*" | cut -d' ' -f2)
                printf "    Bid: %-8s Ask: %s\n" "$BID" "$ASK"
            fi
        done
    else
        echo "  No feed data available"
    fi
    
    # Data Statistics
    echo ""
    echo -e "${CYAN}Database Activity:${NC}"
    
    # Get recent record count
    RECENT_COUNT=$(curl -s -G "http://localhost:9000/exec" \
        --data-urlencode "query=SELECT count(*) FROM ohlc_1m_v2 WHERE timestamp > dateadd('m', -10, now())" \
        2>/dev/null | grep -o '"dataset":\[\[[0-9]*' | grep -o '[0-9]*' | tail -1)
    
    if [ -n "$RECENT_COUNT" ]; then
        printf "  %-20s: %s records\n" "Last 10 minutes" "$(format_number $RECENT_COUNT)"
    fi
    
    # System Resources
    echo ""
    echo -e "${CYAN}System Resources:${NC}"
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    DISK_USAGE=$(df -h ~ | tail -1 | awk '{print $5}')
    
    printf "  %-20s: %.1f%%\n" "CPU Usage" "$CPU_USAGE"
    printf "  %-20s: %.1f%%\n" "Memory Usage" "$MEM_USAGE"
    printf "  %-20s: %s\n" "Disk Usage (home)" "$DISK_USAGE"
    
    # Footer with commands
    echo ""
    echo -e "${BLUE}─────────────────────────────────────────────${NC}"
    echo "Commands: [L]ogs  [S]top All  [R]estart  [Q]uit"
    echo -n "Refreshing in 5 seconds... "
    
    # Read user input with timeout
    read -t 5 -n 1 key
    case $key in
        l|L)
            echo ""
            echo "Opening logs..."
            tail -f $RUNTIME_LOG_DIR/*.log
            ;;
        s|S)
            echo ""
            ~/SPtrader/stop_all.sh
            exit 0
            ;;
        r|R)
            echo ""
            ~/SPtrader/stop_all.sh
            sleep 2
            ~/SPtrader/start_background.sh
            ;;
        q|Q)
            echo ""
            exit 0
            ;;
    esac
done