#!/bin/bash
# Add Go to PATH permanently

echo "🔧 Adding Go to PATH..."
echo ""

# Check if Go is installed
if [ ! -d "/usr/local/go" ]; then
    echo "❌ Go is not installed at /usr/local/go"
    echo "   Please run: ./install_go.sh first"
    exit 1
fi

# Add to .bashrc if not already there
if ! grep -q "/usr/local/go/bin" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Go programming language" >> ~/.bashrc
    echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.bashrc
    echo "✅ Added Go to ~/.bashrc"
else
    echo "ℹ️  Go already in ~/.bashrc"
fi

# Also add to .profile for non-interactive shells
if ! grep -q "/usr/local/go/bin" ~/.profile 2>/dev/null; then
    echo "" >> ~/.profile
    echo "# Go programming language" >> ~/.profile
    echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.profile
    echo "✅ Added Go to ~/.profile"
else
    echo "ℹ️  Go already in ~/.profile"
fi

echo ""
echo "✅ Done! Now run:"
echo ""
echo "   source ~/.bashrc"
echo ""
echo "Or for this session only:"
echo ""
echo "   export PATH=\$PATH:/usr/local/go/bin"
echo ""
echo "Then verify with: go version"