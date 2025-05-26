#!/bin/bash
# Update sptrader CLI to use Go API endpoints

echo "🔄 Updating sptrader CLI for Go API..."

# Backup original
cp sptrader sptrader.python-backup

# Update API endpoints in sptrader
sed -i 's|http://localhost:8000/api/|http://localhost:8080/api/v1/|g' sptrader
sed -i 's|http://localhost:8000/docs|http://localhost:8080/api/v1/contract|g' sptrader

# Update start command to use Go
sed -i 's|"$SPTRADER_HOME/start_background.sh"|"$SPTRADER_HOME/start_go_services.sh"|g' sptrader

# Create start_go_services.sh
cat > start_go_services.sh << 'EOF'
#!/bin/bash
# Start SPtrader services with Go API

echo "🚀 Starting SPtrader services (Go Edition)..."

# Start QuestDB
echo "Starting QuestDB..."
cd ~/questdb && ./questdb.sh start
sleep 5

# Start Go API
echo "Starting Go API..."
cd ~/SPtrader && ./build/sptrader-api &
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
EOF

chmod +x start_go_services.sh

# Also update check_services.sh to check Go API
echo ""
echo "📝 Updating check_services.sh..."
sed -i 's|pgrep -f "uvicorn.*main:app"|pgrep -f "sptrader-api"|g' tools/check_services.sh
sed -i 's|FastAPI|Go API|g' tools/check_services.sh
sed -i 's|http://localhost:8000/api/health|http://localhost:8080/api/v1/health|g' tools/check_services.sh

# Update monitor.sh
echo "📝 Updating monitor.sh..."
sed -i 's|http://localhost:8000/api/|http://localhost:8080/api/v1/|g' tools/monitor.sh
sed -i 's|pgrep -f "uvicorn.*main:app"|pgrep -f "sptrader-api"|g' tools/monitor.sh

# Update test_connectivity.sh
echo "📝 Updating test_connectivity.sh..."
sed -i 's|http://localhost:8000|http://localhost:8080|g' tools/test_connectivity.sh
sed -i 's|/api/health|/api/v1/health|g' tools/test_connectivity.sh

echo ""
echo "✅ CLI updated for Go API!"
echo ""
echo "Changes made:"
echo "  - API endpoints: localhost:8000 → localhost:8080"
echo "  - API paths: /api/ → /api/v1/"
echo "  - Docs URL: /docs → /api/v1/contract"
echo "  - Start script: uses Go API instead of Python"
echo "  - Service checks: look for sptrader-api process"
echo ""
echo "Next steps:"
echo "1. Stop any running Python services: sptrader stop"
echo "2. Start with Go: sptrader start"
echo "3. Check status: sptrader status"