#!/bin/bash
# Install Go 1.21.5 for SPtrader

echo "🚀 Installing Go 1.21.5..."

# Download Go
wget -q https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# Install Go (requires sudo)
echo "Installing to /usr/local (requires sudo password)..."
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# Clean up
rm go1.21.5.linux-amd64.tar.gz

# Add to PATH
echo ""
echo "✅ Go installed!"
echo ""
echo "Add this to your ~/.bashrc or ~/.profile:"
echo 'export PATH=$PATH:/usr/local/go/bin'
echo ""
echo "Then run:"
echo "source ~/.bashrc"
echo ""
echo "Or for this session only:"
echo "export PATH=\$PATH:/usr/local/go/bin"
echo ""
echo "Verify with: go version"