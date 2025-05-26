#!/bin/bash
# Quick fix for missing data_source column issue

echo "🔧 Fixing missing data_source column..."

# Add column to market_data table
curl -G "http://localhost:9000/exec" \
  --data-urlencode "query=ALTER TABLE market_data ADD COLUMN IF NOT EXISTS data_source SYMBOL" \
  2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Added data_source column to market_data table"
else
    echo "❌ Failed to add column (may already exist)"
fi

# Update existing records
curl -G "http://localhost:9000/exec" \
  --data-urlencode "query=UPDATE market_data SET data_source = 'oanda' WHERE data_source IS NULL" \
  2>/dev/null

echo "✅ Updated existing records with 'oanda' source"
echo ""
echo "📝 Next: Update oanda_feed.py to include data_source in INSERT statements"