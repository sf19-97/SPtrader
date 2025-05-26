#!/bin/bash
#
# install_cli.sh - SPtrader CLI Installation Script
#
# Description:
#   Installs the sptrader command-line interface for system-wide access.
#   This script creates a symlink in ~/.local/bin and ensures it's in your PATH,
#   allowing you to run 'sptrader' from anywhere in your terminal.
#
# What it does:
#   1. Creates ~/.local/bin directory if it doesn't exist
#   2. Creates symlink: ~/.local/bin/sptrader -> ~/SPtrader/sptrader
#   3. Checks if ~/.local/bin is in your PATH
#   4. Adds PATH export to shell config files if needed (.bashrc, .zshrc)
#
# Installation Process:
#   - Non-destructive: Won't duplicate PATH entries if already present
#   - Multi-shell support: Updates both bash and zsh configs if found
#   - Safe symlink: Uses -f flag to overwrite existing symlink
#
# After Installation:
#   - New terminals will have 'sptrader' command available
#   - Current terminal needs: source ~/.bashrc (or ~/.zshrc)
#   - Alternative: Just start a new terminal session
#
# Usage:
#   ./install_cli.sh    # Run once to install
#
# Verification:
#   which sptrader      # Should show ~/.local/bin/sptrader
#   sptrader help       # Should display help menu
#
# Note:
#   This installation is per-user, not system-wide. Each user needs
#   to run this script to get the sptrader command.

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Installing SPtrader CLI...${NC}"

# Create local bin directory
mkdir -p ~/.local/bin

# Create symlink
ln -sf ~/SPtrader/sptrader ~/.local/bin/sptrader

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}Adding ~/.local/bin to PATH...${NC}"
    
    # Add to appropriate shell config
    if [ -f ~/.bashrc ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo -e "${GREEN}✓ Added to ~/.bashrc${NC}"
    fi
    
    if [ -f ~/.zshrc ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo -e "${GREEN}✓ Added to ~/.zshrc${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Please run one of the following to update your PATH:${NC}"
    echo "  source ~/.bashrc    # For bash"
    echo "  source ~/.zshrc     # For zsh"
    echo ""
    echo -e "${YELLOW}Or start a new terminal session.${NC}"
else
    echo -e "${GREEN}✓ ~/.local/bin is already in PATH${NC}"
fi

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "You can now use the 'sptrader' command from anywhere:"
echo "  sptrader start      # Start all services"
echo "  sptrader status     # Check status"
echo "  sptrader help       # Show all commands"