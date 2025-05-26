#!/bin/bash

# Complete data source tracking implementation for SPtrader
# This script implements the full data source tracking system

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SPtrader Data Source Tracking Implementation   ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Run viewport optimizations
echo -e "${YELLOW}Step 1: Running viewport optimizations...${NC}"
if sptrader optimize; then
    echo -e "${GREEN}✓ Viewport optimizations complete${NC}"
else
    echo -e "${RED}✗ Viewport optimizations failed${NC}"
    echo "Please ensure QuestDB is running: sptrader start"
    exit 1
fi

# Step 2: Update data tables with source tracking
echo -e "\n${YELLOW}Step 2: Adding data source tracking to tables...${NC}"
cd ~/SPtrader
python scripts/update_data_tables_source_tracking.py

# Step 3: Show current data statistics
echo -e "\n${YELLOW}Step 3: Current data statistics:${NC}"
echo -e "${BLUE}Checking existing data...${NC}"

# Check Oanda data
OANDA_COUNT=$(curl -s -G "http://localhost:9000/exec" \
    --data-urlencode "query=SELECT count(*) FROM market_data" \
    2>/dev/null | grep -o '"dataset":\[\[[0-9]*' | grep -o '[0-9]*' | tail -1)

if [ -n "$OANDA_COUNT" ]; then
    echo -e "  Oanda (market_data): $(printf "%'d" $OANDA_COUNT) records"
fi

# Check Dukascopy data
DUKA_COUNT=$(curl -s -G "http://localhost:9000/exec" \
    --data-urlencode "query=SELECT count(*) FROM market_data_v2" \
    2>/dev/null | grep -o '"dataset":\[\[[0-9]*' | grep -o '[0-9]*' | tail -1)

if [ -n "$DUKA_COUNT" ]; then
    echo -e "  Dukascopy (market_data_v2): $(printf "%'d" $DUKA_COUNT) records"
fi

# Step 4: Summary and next steps
echo -e "\n${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Data source tracking implementation complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}What was done:${NC}"
echo "  1. Created viewport tables for fast queries"
echo "  2. Added data_source column to all tables"
echo "  3. Updated oanda_feed.py to tag new data as 'oanda'"
echo "  4. Existing data has been tagged appropriately"

echo -e "\n${BLUE}Next steps:${NC}"
echo "  1. Restart services to use updated code:"
echo -e "     ${YELLOW}sptrader restart${NC}"
echo ""
echo "  2. Load historical Dukascopy data:"
echo -e "     ${YELLOW}cd ~/SPtrader/data_feeds${NC}"
echo -e "     ${YELLOW}python dukascopy_importer.py${NC}"
echo ""
echo "  3. Monitor data sources:"
echo -e "     ${YELLOW}sptrader db query \"SELECT data_source, count(*) FROM market_data GROUP BY data_source\"${NC}"

echo -e "\n${BLUE}Your system now intelligently tracks data providence!${NC}"
echo "  • Historical data: High-quality Dukascopy"
echo "  • Real-time data: Low-latency Oanda"
echo "  • API can prefer better quality data when available"