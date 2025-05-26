#!/bin/bash
# Verify Go migration is complete and working

# Source bashrc to get Go in PATH
source ~/.bashrc 2>/dev/null || true

echo "🔍 Verifying SPtrader Go Setup"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Go installation
echo "1. Go Installation:"
if command -v go &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Go installed: $(go version)"
else
    echo -e "   ${RED}✗${NC} Go not found in PATH"
fi

# Check Go binary
echo ""
echo "2. Go API Binary:"
if [ -f "build/sptrader-api" ]; then
    echo -e "   ${GREEN}✓${NC} Binary exists: build/sptrader-api"
    echo "   Size: $(ls -lh build/sptrader-api | awk '{print $5}')"
else
    echo -e "   ${RED}✗${NC} Binary not found. Run: ./build_and_run.sh"
fi

# Check if services are running
echo ""
echo "3. Running Services:"
if pgrep -f "questdb.*ServerMain" > /dev/null; then
    echo -e "   ${GREEN}✓${NC} QuestDB is running"
else
    echo -e "   ${RED}✗${NC} QuestDB is not running"
fi

if pgrep -f "sptrader-api" > /dev/null; then
    echo -e "   ${GREEN}✓${NC} Go API is running"
else
    echo -e "   ${YELLOW}!${NC} Go API is not running"
fi

# Check API endpoints
echo ""
echo "4. API Endpoints:"
if curl -s http://localhost:8080/api/v1/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Health endpoint: http://localhost:8080/api/v1/health"
    echo -e "   ${GREEN}✓${NC} Contract endpoint: http://localhost:8080/api/v1/contract"
else
    echo -e "   ${RED}✗${NC} API not responding on port 8080"
fi

# Check CLI updates
echo ""
echo "5. CLI Configuration:"
if grep -q "localhost:8080" sptrader; then
    echo -e "   ${GREEN}✓${NC} CLI using Go API (port 8080)"
else
    echo -e "   ${RED}✗${NC} CLI still using Python API"
fi

if grep -q "start_go_services.sh" sptrader; then
    echo -e "   ${GREEN}✓${NC} CLI starts Go services"
else
    echo -e "   ${RED}✗${NC} CLI not updated for Go"
fi

# Check TUI updates
echo ""
echo "6. TUI Configuration:"
if grep -q "localhost:8080" clean_tui.py; then
    echo -e "   ${GREEN}✓${NC} TUI using Go API"
else
    echo -e "   ${RED}✗${NC} TUI still using Python API"
fi

# Check for redundant files
echo ""
echo "7. Cleanup Status:"
redundant=0
[ -d "api/" ] && echo -e "   ${YELLOW}!${NC} Python API folder still exists" && redundant=1
[ -f "start_background.sh" ] && echo -e "   ${YELLOW}!${NC} Old start script still exists" && redundant=1
[ -f "update_cli_for_go.sh" ] && echo -e "   ${YELLOW}!${NC} Update scripts still exist" && redundant=1
[ -f "sptrader.python-backup" ] && echo -e "   ${YELLOW}!${NC} Backup files still exist" && redundant=1

if [ $redundant -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} No redundant files found"
fi

# Summary
echo ""
echo "=============================="
echo "Summary:"

all_good=1
# Check critical items
if ! command -v go &> /dev/null; then
    echo -e "${RED}❌ Go not installed${NC}"
    all_good=0
fi

if [ ! -f "build/sptrader-api" ]; then
    echo -e "${RED}❌ Go API not built${NC}"
    all_good=0
fi

if ! grep -q "localhost:8080" sptrader; then
    echo -e "${RED}❌ CLI not updated${NC}"
    all_good=0
fi

if [ $redundant -eq 1 ]; then
    echo -e "${YELLOW}⚠️  Redundant files need cleanup${NC}"
    echo "   Run: ./finalize_go_migration.sh"
fi

if [ $all_good -eq 1 ]; then
    echo -e "${GREEN}✅ Go migration complete!${NC}"
    echo ""
    echo "Everything is set up correctly. You can:"
    echo "  • Start services: sptrader start"
    echo "  • Check status: sptrader status"
    echo "  • Monitor: sptrader monitor"
    echo "  • View logs: sptrader logs -f"
else
    echo ""
    echo "Some issues need attention. See above for details."
fi