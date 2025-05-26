#!/bin/bash
#
# dashboard.sh - SPtrader Quick Status Dashboard (Legacy)
#
# Description:
#   Legacy dashboard script that shows a quick overview of the SPtrader system.
#   This script is from the older architecture that used CORS proxy and Python HTTP server.
#   
#   NOTE: This script is deprecated in favor of:
#   - sptrader status    # For comprehensive service status
#   - sptrader monitor   # For real-time monitoring dashboard
#
# What it shows:
#   - Link to the old forex chart (now in deprecated/)
#   - Latest prices for EURUSD and GBPUSD from market_data table
#   - Total tick count in the database
#   - Count of running services (uses old service names)
#
# Limitations:
#   - References old chart URL that no longer exists
#   - Counts old services (cors_proxy) instead of new ones (FastAPI)
#   - Limited to 2 currency pairs
#   - No health checks or performance metrics
#
# Usage:
#   ./dashboard.sh       # Direct execution (not recommended)
#   
# Recommended alternatives:
#   sptrader status      # Full service status with health checks
#   sptrader monitor     # Interactive real-time dashboard

echo "=== SPtrader Dashboard ==="
echo "Chart: http://localhost:8080/forex_chart.html"
echo ""
echo "Latest Prices:"
curl -s -G "http://localhost:9000/exec" \
  --data-urlencode "query=SELECT symbol, price, timestamp FROM market_data WHERE symbol IN ('EURUSD','GBPUSD') ORDER BY timestamp DESC LIMIT 2" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); [print(f'{r[1]}: {r[2]:.5f}') for r in d['dataset']]" 2>/dev/null

echo ""
echo "Record Count:"
curl -s -G "http://localhost:9000/exec" \
  --data-urlencode "query=SELECT count(*) as total FROM market_data" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Total ticks: {d['dataset'][0][0]}\")" 2>/dev/null

echo ""
echo "Services: $(ps aux | grep -E '(oanda|ohlc|cors|questdb)' | grep -v grep | wc -l)/5 running"
