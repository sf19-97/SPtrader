#!/bin/bash
# Finalize Go migration - clean up redundant files and folders

echo "🧹 Finalizing Go Migration - Cleanup"
echo "===================================="

# Check if Go API is running
if pgrep -f "sptrader-api" > /dev/null; then
    echo "✅ Go API is running"
else
    echo "⚠️  Go API is not running. Start it with: ./build_and_run.sh"
fi

echo ""
echo "📁 Files/Folders to Clean Up:"
echo ""

# 1. Python API folder (replaced by Go)
if [ -d "api/" ]; then
    echo "  • api/ - Python FastAPI (replaced by Go)"
    echo "    Contains: main.py, test_api.py, requirements.txt, venv/"
fi

# 2. Update scripts (no longer needed after migration)
echo "  • update_cli_for_go.sh - Already applied"
echo "  • update_tui_for_go.sh - Already applied"
echo "  • install_go.sh - Go is installed"

# 3. Backup files
echo "  • sptrader.python-backup - Backup of old CLI"
echo "  • clean_tui.py.python-backup - Backup of old TUI"

# 4. Old start script
echo "  • start_background.sh - Replaced by start_go_services.sh"

# 5. Download artifact
echo "  • go1.21.5.linux-amd64.tar.gz.1 - Go installer download"

# 6. Empty directories
echo "  • tui/ - Contains only redundant chart-user-workflow.md"

# 7. Duplicate documentation
echo "  • CLI_README.md - Redundant with main README"
echo "  • README_GO.md - Should be merged into main README"

echo ""
echo "🤔 Confirm cleanup? This will:"
echo "  1. Move Python API to deprecated/python-api/"
echo "  2. Remove update/install scripts"
echo "  3. Remove backup files"
echo "  4. Clean up empty directories"
echo "  5. Consolidate documentation"
echo ""
read -p "Proceed with cleanup? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🚀 Starting cleanup..."

# Create deprecated folder structure
mkdir -p deprecated/python-api
mkdir -p deprecated/migration-scripts

# 1. Move Python API
if [ -d "api/" ]; then
    echo "Moving Python API to deprecated/..."
    mv api/ deprecated/python-api/
fi

# 2. Move migration scripts
echo "Moving migration scripts..."
[ -f "update_cli_for_go.sh" ] && mv update_cli_for_go.sh deprecated/migration-scripts/
[ -f "update_tui_for_go.sh" ] && mv update_tui_for_go.sh deprecated/migration-scripts/
[ -f "install_go.sh" ] && mv install_go.sh deprecated/migration-scripts/
[ -f "scripts/migrate_to_go.sh" ] && mv scripts/migrate_to_go.sh deprecated/migration-scripts/

# 3. Remove backups
echo "Removing backup files..."
[ -f "sptrader.python-backup" ] && rm sptrader.python-backup
[ -f "clean_tui.py.python-backup" ] && rm clean_tui.py.python-backup

# 4. Move old start script
[ -f "start_background.sh" ] && mv start_background.sh deprecated/

# 5. Remove Go installer
[ -f "go1.21.5.linux-amd64.tar.gz.1" ] && rm go1.21.5.linux-amd64.tar.gz.1

# 6. Clean empty tui directory
if [ -d "tui/" ] && [ -f "tui/chart-user-workflow.md" ]; then
    rm -rf tui/
fi

# 7. Update documentation
echo "Consolidating documentation..."

# Create new README header
cat > README.new.md << 'EOF'
# SPtrader - High-Performance Forex Trading Platform (Go Edition)

A professional forex trading platform with real-time data feeds, high-performance charting, and viewport-aware data streaming.

**Now powered by Go!** - Migrated from Python for better performance, type safety, and concurrent handling.

## 🚀 Quick Start

### Prerequisites
- Go 1.21+ (installed)
- QuestDB (included)
- Some market data loaded

### Start Trading
```bash
sptrader start    # Start all services (Go API + QuestDB)
sptrader monitor  # Watch real-time dashboard
```

Visit:
- API Health: http://localhost:8080/api/v1/health
- Data Contract: http://localhost:8080/api/v1/contract
- QuestDB Console: http://localhost:9000

EOF

# Append rest of original README (skipping old quick start)
tail -n +20 README.md >> README.new.md

# Add Go-specific sections from README_GO
echo "" >> README.new.md
echo "## 🏗️ Architecture (Go Implementation)" >> README.new.md
echo "" >> README.new.md
grep -A 50 "Clean Architecture" README_GO.md >> README.new.md

# Replace old README
mv README.md deprecated/README.python.md
mv README.new.md README.md

# Move other redundant docs
[ -f "CLI_README.md" ] && mv CLI_README.md deprecated/
[ -f "README_GO.md" ] && mv README_GO.md deprecated/

echo ""
echo "✅ Cleanup Complete!"
echo ""
echo "📊 Summary:"
echo "  - Python API moved to: deprecated/python-api/"
echo "  - Migration scripts moved to: deprecated/migration-scripts/"
echo "  - Documentation consolidated into README.md"
echo "  - Backups and temporary files removed"
echo ""
echo "🎯 Your Go-powered SPtrader is ready!"
echo "  - API: http://localhost:8080"
echo "  - Use 'sptrader' CLI for all operations"
echo "  - Run 'sptrader help' for commands"