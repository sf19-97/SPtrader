#!/bin/bash
# Migrate from Python FastAPI to Go Gin

echo "🚀 SPtrader Migration to Go"
echo "=========================="

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed. Please install Go 1.21 or later"
    exit 1
fi

echo "✅ Go version: $(go version)"

# Stop existing Python services
echo ""
echo "📦 Stopping Python services..."
if [ -f "stop_all.sh" ]; then
    ./stop_all.sh
fi

# Build Go API
echo ""
echo "🔨 Building Go API..."
make build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"

# Update start script to use Go API
echo ""
echo "📝 Creating new start script..."
cat > start_go_services.sh << 'EOF'
#!/bin/bash
# Start SPtrader services with Go API

echo "🚀 Starting SPtrader services (Go Edition)..."

# Start QuestDB
echo "Starting QuestDB..."
cd ~/questdb && ./questdb.sh start &
sleep 5

# Start Go API
echo "Starting Go API..."
cd ~/SPtrader && ./build/sptrader-api &

# Start data feeds (still Python for now)
echo "Starting data feeds..."
cd ~/SPtrader/data_feeds && python oanda_feed.py &
cd ~/SPtrader/scripts && python ohlc_manager.py &

echo "✅ All services started"
echo ""
echo "Services:"
echo "  - QuestDB: http://localhost:9000"
echo "  - API (Go): http://localhost:8080"
echo "  - API Docs: http://localhost:8080/api/v1/contract"
EOF

chmod +x start_go_services.sh

# Update sptrader CLI to point to new API
echo ""
echo "📝 Updating sptrader CLI..."
sed -i 's/localhost:8000/localhost:8080/g' sptrader
sed -i 's|/api/|/api/v1/|g' sptrader

# Create systemd service
echo ""
echo "📝 Creating systemd service..."
cat > sptrader-api.service << 'EOF'
[Unit]
Description=SPtrader Go API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/SPtrader
ExecStart=/home/$USER/SPtrader/build/sptrader-api
Restart=always
RestartSec=10
Environment="GIN_MODE=release"

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "✅ Migration preparation complete!"
echo ""
echo "Next steps:"
echo "1. Test the Go API:"
echo "   make dev"
echo ""
echo "2. Profile your data:"
echo "   go run cmd/profiler/main.go"
echo ""
echo "3. Start services with Go:"
echo "   ./start_go_services.sh"
echo ""
echo "4. Test endpoints:"
echo "   curl http://localhost:8080/api/v1/health"
echo "   curl http://localhost:8080/api/v1/contract"
echo ""
echo "5. For production:"
echo "   sudo cp sptrader-api.service /etc/systemd/system/"
echo "   sudo systemctl enable sptrader-api"
echo "   sudo systemctl start sptrader-api"