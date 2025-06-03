#!/bin/bash
# Start services with LOCKED ports

echo "=== LOCKED PORT STARTUP ==="

# 1. Murder anything on our ports
echo "Clearing ports..."
fuser -k 8080/tcp 2>/dev/null
fuser -k 9000/tcp 2>/dev/null
sleep 2

# 2. Start QuestDB
echo "Starting QuestDB on port 9000..."
cd ~/questdb-8.3.1-rt-linux-x86-64
./bin/questdb.sh start
sleep 5

# 3. Start API with explicit port binding
echo "Starting API on port 8080..."
cd ~/SPtrader
export GIN_MODE=release
export PORT=8080
nohup ./cmd/api/api > logs/api.log 2>&1 &
API_PID=$!
sleep 3

# 4. Verify and LOCK
echo ""
echo "Verification:"
if lsof -ti:9000 >/dev/null; then
    echo "✅ QuestDB locked on port 9000"
else
    echo "❌ QuestDB failed!"
    exit 1
fi

if kill -0 $API_PID 2>/dev/null; then
    echo "✅ API locked on port 8080 (PID: $API_PID)"
    echo $API_PID > /tmp/sptrader_api.pid
else
    echo "❌ API failed to start!"
    exit 1
fi

# 5. Create a stop script that uses the PID
cat > ~/SPtrader/stop_locked.sh << EOF
#!/bin/bash
echo "Stopping locked services..."
if [ -f /tmp/sptrader_api.pid ]; then
    kill \$(cat /tmp/sptrader_api.pid) 2>/dev/null
    rm /tmp/sptrader_api.pid
fi
pkill -f questdb
echo "Done"
EOF
chmod +x ~/SPtrader/stop_locked.sh

echo ""
echo "✅ Services started with LOCKED ports!"
echo "✅ Use ./stop_locked.sh to stop them"
echo ""
echo "If anything tries to steal port 8080, find it with:"
echo "  lsof -i :8080"