#!/bin/bash
#
# Direct Database Access Tool for SPtrader
# Provides raw access to QuestDB structure and data
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPTRADER_HOME="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# QuestDB connection details
DB_HOST="localhost"
DB_PORT="8812"  # PostgreSQL wire protocol port

function check_psql() {
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}psql not found. Installing...${NC}"
        sudo apt-get update && sudo apt-get install -y postgresql-client
    fi
}

function show_tables() {
    echo -e "${BLUE}=== Database Tables ===${NC}"
    PGPASSWORD=quest psql -h $DB_HOST -p $DB_PORT -U admin -d qdb -t -c "
        SELECT table_name 
        FROM tables() 
        ORDER BY table_name;"
}

function show_table_structure() {
    local table=$1
    echo -e "${BLUE}=== Structure of $table ===${NC}"
    PGPASSWORD=quest psql -h $DB_HOST -p $DB_PORT -U admin -d qdb -c "
        SELECT 
            column AS column_name,
            type AS data_type,
            indexed
        FROM table_columns('$table')
        ORDER BY column;"
}

function show_data_summary() {
    local table=$1
    echo -e "${BLUE}=== Data Summary for $table ===${NC}"
    PGPASSWORD=quest psql -h $DB_HOST -p $DB_PORT -U admin -d qdb -c "
        SELECT 
            symbol,
            MIN(timestamp) as first_record,
            MAX(timestamp) as last_record,
            COUNT(*) as total_records
        FROM $table
        GROUP BY symbol
        ORDER BY symbol;"
}

function show_recent_data() {
    local table=$1
    local symbol=${2:-EURUSD}
    echo -e "${BLUE}=== Recent Data for $symbol in $table ===${NC}"
    PGPASSWORD=quest psql -h $DB_HOST -p $DB_PORT -U admin -d qdb -c "
        SELECT * 
        FROM $table
        WHERE symbol = '$symbol'
        ORDER BY timestamp DESC
        LIMIT 10;"
}

function check_data_gaps() {
    local table=$1
    local symbol=${2:-EURUSD}
    echo -e "${BLUE}=== Checking Data Gaps for $symbol ===${NC}"
    PGPASSWORD=quest psql -h $DB_HOST -p $DB_PORT -U admin -d qdb -c "
        WITH time_diffs AS (
            SELECT 
                timestamp,
                timestamp - LAG(timestamp) OVER (ORDER BY timestamp) as gap,
                bid, ask
            FROM $table
            WHERE symbol = '$symbol'
            ORDER BY timestamp DESC
            LIMIT 1000
        )
        SELECT 
            timestamp,
            gap,
            bid,
            ask
        FROM time_diffs
        WHERE gap > '1 minute'::interval
        ORDER BY gap DESC
        LIMIT 20;"
}

function raw_query() {
    local query=$1
    echo -e "${BLUE}=== Executing Query ===${NC}"
    echo -e "${YELLOW}$query${NC}"
    PGPASSWORD=quest psql -h $DB_HOST -p $DB_PORT -U admin -d qdb -c "$query"
}

function interactive_console() {
    echo -e "${GREEN}Opening QuestDB Interactive Console...${NC}"
    echo -e "${YELLOW}Connection: psql -h $DB_HOST -p $DB_PORT -U admin -d qdb${NC}"
    echo -e "${YELLOW}Password: quest${NC}"
    PGPASSWORD=quest psql -h $DB_HOST -p $DB_PORT -U admin -d qdb
}

# Main menu
case "$1" in
    "tables")
        check_psql
        show_tables
        ;;
    "structure")
        check_psql
        show_table_structure "${2:-market_data_v2}"
        ;;
    "summary")
        check_psql
        show_data_summary "${2:-market_data_v2}"
        ;;
    "recent")
        check_psql
        show_recent_data "${2:-market_data_v2}" "${3:-EURUSD}"
        ;;
    "gaps")
        check_psql
        check_data_gaps "${2:-market_data_v2}" "${3:-EURUSD}"
        ;;
    "query")
        check_psql
        raw_query "$2"
        ;;
    "console")
        check_psql
        interactive_console
        ;;
    *)
        echo -e "${YELLOW}Direct Database Access Commands:${NC}"
        echo -e "  ${GREEN}sptrader db tables${NC}           - List all tables"
        echo -e "  ${GREEN}sptrader db structure [table]${NC} - Show table structure"
        echo -e "  ${GREEN}sptrader db summary [table]${NC}   - Show data summary by symbol"
        echo -e "  ${GREEN}sptrader db recent [table] [symbol]${NC} - Show recent records"
        echo -e "  ${GREEN}sptrader db gaps [table] [symbol]${NC}   - Check for data gaps"
        echo -e "  ${GREEN}sptrader db query \"SQL\"${NC}      - Run raw SQL query"
        echo -e "  ${GREEN}sptrader db console${NC}          - Open interactive console"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo -e "  sptrader db structure market_data_v2"
        echo -e "  sptrader db summary market_data_v2"
        echo -e "  sptrader db recent market_data_v2 EURUSD"
        echo -e "  sptrader db query \"SELECT COUNT(*) FROM market_data_v2\""
        ;;
esac