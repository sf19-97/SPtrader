#!/bin/bash
# Update clean_tui.py to use Go API

echo "🔄 Updating TUI for Go API..."

# Backup original
cp clean_tui.py clean_tui.py.python-backup

# Update API endpoints
sed -i 's|http://localhost:8000/api/health|http://localhost:8080/api/v1/health|g' clean_tui.py
sed -i 's|http://localhost:8000/api/stats|http://localhost:8080/api/v1/stats|g' clean_tui.py
sed -i 's|pgrep -f .uvicorn.*main:app.|pgrep -f .sptrader-api.|g' clean_tui.py
sed -i 's|FastAPI|Go API|g' clean_tui.py

echo "✅ TUI updated for Go API!"