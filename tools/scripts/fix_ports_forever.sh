#!/bin/bash
# Fix the fucking ports once and for all

echo "=== FIXING PORTS PERMANENTLY ==="

# 1. Kill EVERYTHING using our ports
echo "Killing everything on ports 8080, 8000, 9000..."
for port in 8080 8000 9000; do
    lsof -ti:$port | xargs -r kill -9 2>/dev/null
done

# 2. Check Electron app config
echo ""
echo "Checking Electron configuration..."
ELECTRON_MAIN="/home/millet_frazier/SPtrader/frontend/main.js"
if grep -q "8080" "$ELECTRON_MAIN"; then
    echo "❌ WARNING: Electron main.js contains port 8080!"
    echo "   This might be causing conflicts!"
    grep -n "8080" "$ELECTRON_MAIN"
fi

# 3. Create systemd service files to lock the ports
echo ""
echo "Creating systemd services to lock ports..."

# QuestDB service
sudo tee /etc/systemd/system/sptrader-questdb.service > /dev/null << 'EOF'
[Unit]
Description=SPtrader QuestDB
After=network.target

[Service]
Type=forking
User=millet_frazier
WorkingDirectory=/home/millet_frazier/questdb-8.3.1-rt-linux-x86-64
ExecStart=/home/millet_frazier/questdb-8.3.1-rt-linux-x86-64/bin/questdb.sh start
ExecStop=/home/millet_frazier/questdb-8.3.1-rt-linux-x86-64/bin/questdb.sh stop
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# API service
sudo tee /etc/systemd/system/sptrader-api.service > /dev/null << 'EOF'
[Unit]
Description=SPtrader Go API
After=network.target sptrader-questdb.service
Requires=sptrader-questdb.service

[Service]
Type=simple
User=millet_frazier
WorkingDirectory=/home/millet_frazier/SPtrader
ExecStart=/home/millet_frazier/SPtrader/cmd/api/api
Restart=on-failure
RestartSec=5
Environment="GIN_MODE=release"

# Lock the port
Environment="PORT=8080"
Environment="LISTEN_ADDR=:8080"

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created systemd services"

# 4. Create a port guardian script
cat > /home/millet_frazier/SPtrader/scripts/port_guardian.sh << 'EOF'
#!/bin/bash
# Port guardian - kills anything that tries to steal our ports

PROTECTED_PORTS="8080 9000"

while true; do
    for port in $PROTECTED_PORTS; do
        # Check if our services are using the ports
        API_PID=$(pgrep -f "cmd/api/api")
        QUESTDB_PID=$(pgrep -f "questdb.*ServerMain")
        
        # Kill anything else using our ports
        INTRUDERS=$(lsof -ti:$port | grep -v -E "^($API_PID|$QUESTDB_PID)$")
        if [ ! -z "$INTRUDERS" ]; then
            echo "$(date): Killing intruder on port $port: $INTRUDERS"
            echo "$INTRUDERS" | xargs kill -9
        fi
    done
    sleep 5
done
EOF

chmod +x /home/millet_frazier/SPtrader/scripts/port_guardian.sh

echo ""
echo "=== SOLUTION ==="
echo ""
echo "Option 1: Use systemd services (recommended):"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable sptrader-questdb sptrader-api"
echo "  sudo systemctl start sptrader-questdb sptrader-api"
echo ""
echo "Option 2: Run the port guardian in background:"
echo "  nohup /home/millet_frazier/SPtrader/scripts/port_guardian.sh > /dev/null 2>&1 &"
echo ""
echo "Option 3: Fix Electron to use a different port"
echo "  Edit frontend/main.js if it's binding to 8080"