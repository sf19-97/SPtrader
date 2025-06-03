#!/bin/bash
# QuestDB CLI setup script
# Created: May 31, 2025

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================="
echo "  QuestDB CLI Setup"
echo "========================================="
echo "This script will set up the QuestDB CLI tool."
echo

# Ensure we're in the right directory
cd "$SCRIPT_DIR"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "Please install Node.js v16+ and try again."
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed."
    echo "Please install npm and try again."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Ensure directories exist
echo "📁 Creating required directories..."
mkdir -p config output templates scripts logs

# Make scripts executable
echo "🔧 Setting permissions..."
chmod +x questdb-cli.js questdb-cli.sh

# Run configuration
echo
echo "📝 Running configuration setup..."
node questdb-cli.js config --setup

echo
echo "✅ Setup complete!"
echo "You can now use QuestDB CLI with:"
echo "  ./questdb-cli.sh"
echo