#!/bin/bash
# Start SPtrader services with Go API

echo "🚀 Starting SPtrader services (Go Edition)..."

# Start QuestDB
echo "Starting QuestDB..."
cd ~/questdb-8.3.1-rt-linux-x86-64/bin && ./questdb.sh start
sleep 5

# Start Go API with environment variable
echo "Starting Go API..."
cd ~/SPtrader && export SPTRADER_HOME=/home/millet_frazier/SPtrader && ./build/sptrader-api &
sleep 2

# Start data feeds (still Python for now)
echo "Starting data feeds..."
cd ~/SPtrader/data_feeds && python oanda_feed.py > ~/SPtrader/logs/runtime/oanda_feed.log 2>&1 &
cd ~/SPtrader/scripts && python ohlc_manager.py > ~/SPtrader/logs/runtime/ohlc_manager.log 2>&1 &

echo "✅ All services started"
echo ""
echo "Services:"
echo "  - QuestDB: http://localhost:9000"
echo "  - API (Go): http://localhost:8080"
echo "  - API Contract: http://localhost:8080/api/v1/contract"
echo ""
echo "Use 'sptrader status' to check service health"
