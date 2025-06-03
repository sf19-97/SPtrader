#!/bin/bash
# fix_electron_sandbox.sh
# Fixes Electron sandbox permissions for SPtrader desktop app
# Created: May 31, 2025
# Last run: Successfully fixed permissions on May 31, 2025

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Fixing Electron sandbox permissions...${NC}"

# Get the frontend directory
FRONTEND_DIR=$(realpath "$(dirname "$0")/../frontend")
SANDBOX_PATH="$FRONTEND_DIR/node_modules/electron/dist/chrome-sandbox"

# Check if the sandbox file exists
if [ ! -f "$SANDBOX_PATH" ]; then
  echo -e "${RED}Error: Chrome sandbox not found at $SANDBOX_PATH${NC}"
  echo -e "${YELLOW}Make sure you have installed electron dependencies:${NC}"
  echo -e "cd $FRONTEND_DIR && npm install"
  exit 1
fi

# Try to set the proper permissions
echo "Setting SUID permissions on $SANDBOX_PATH"
if sudo chown root:root "$SANDBOX_PATH" && sudo chmod 4755 "$SANDBOX_PATH"; then
  echo -e "${GREEN}✓ Successfully fixed Electron sandbox permissions${NC}"
  echo -e "${GREEN}✓ You can now start the Electron app normally${NC}"
else
  echo -e "${RED}Failed to set permissions. You can run Electron with --no-sandbox instead:${NC}"
  echo -e "${YELLOW}cd $FRONTEND_DIR && npm run start -- --no-sandbox${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}Electron app should now work with continuous forex charts!${NC}"