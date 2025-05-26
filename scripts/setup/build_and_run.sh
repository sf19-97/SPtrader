#!/bin/bash
# Build and run SPtrader Go API

echo "🔨 Building SPtrader Go API..."
echo "================================"

# Check if Go is available
GO_BIN="go"
if ! command -v go &> /dev/null; then
    # Try using full path
    if [ -x "/usr/local/go/bin/go" ]; then
        GO_BIN="/usr/local/go/bin/go"
        export PATH=$PATH:/usr/local/go/bin
    else
        echo "❌ Go is not installed or not in PATH"
        echo ""
        echo "Please run: ./install_go.sh"
        echo "Then: export PATH=\$PATH:/usr/local/go/bin"
        exit 1
    fi
fi

echo "✅ Go version: $($GO_BIN version)"
echo ""

# Download dependencies
echo "📦 Downloading dependencies..."
$GO_BIN mod download
$GO_BIN mod tidy

# Build the API
echo ""
echo "🔨 Building API..."
$GO_BIN build -v -o build/sptrader-api cmd/api/main.go

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📊 Binary info:"
    ls -lh build/sptrader-api
    echo ""
    echo "🚀 Starting API..."
    echo "================================"
    echo ""
    
    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 Created .env from .env.example"
        echo ""
    fi
    
    # Run the API
    ./build/sptrader-api
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi