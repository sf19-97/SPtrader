#!/bin/bash

# Start SPtrader Desktop Application
# This script ensures the backend API is running before launching the desktop app

echo "Starting SPtrader Desktop Application..."

# Check if the API is running
if ! curl -s http://localhost:8080/api/health > /dev/null; then
    echo "Warning: API server not detected at http://localhost:8080"
    echo "Please ensure the SPtrader backend is running first."
    echo "You can start it with: cd ~/SPtrader && ./start_go_services.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Navigate to frontend directory
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the Electron app
echo "Launching SPtrader Desktop..."
npm run start-no-sandbox