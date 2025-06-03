#!/bin/bash
# DevTools CLI setup script
# Created: May 31, 2025

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================="
echo "  DevTools CLI Setup"
echo "========================================="
echo "This script will set up the DevTools CLI tool."
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
npm install @inquirer/prompts

# Ensure directories exist
echo "📁 Creating required directories..."
mkdir -p config output

# Make scripts executable
echo "🔧 Setting permissions..."
chmod +x devtools.js devtools-cli.sh

# Run configuration
echo
echo "📝 Running configuration setup..."
node -e "require('./lib/config').setupConfig()"

echo
echo "✅ Setup complete!"
echo "You can now use DevTools CLI with:"
echo "  ./devtools-cli.sh"
echo