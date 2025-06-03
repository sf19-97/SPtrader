#!/bin/bash
# Daily Data Update Script
# Uses the dukascopy command
# Created: May 31, 2025

# Configuration
LOG_DIR="/home/millet_frazier/SPtrader/logs/runtime"
LOG_FILE="$LOG_DIR/daily_update_$(date +%Y%m%d).log"
SYMBOLS=("EURUSD" "GBPUSD" "USDJPY")

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "==============================================="
echo "🕒 Starting daily data update: $(date)"
echo "==============================================="

# Run the unified dukascopy loader
dukascopy daily --symbols "${SYMBOLS[@]}" --generate-ohlc --verify