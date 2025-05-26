#!/bin/bash
# Test the Go API endpoints

API_URL="http://localhost:8080/api/v1"

echo "🧪 Testing SPtrader Go API"
echo "========================="
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    
    echo "Testing: $name"
    echo "URL: $url"
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo "✅ Status: $http_code"
        echo "Response preview:"
        echo "$body" | jq '.' 2>/dev/null | head -20 || echo "$body" | head -20
    else
        echo "❌ Status: $http_code"
        echo "Response: $body"
    fi
    echo ""
    echo "---"
    echo ""
}

# Test health endpoint
test_endpoint "Health Check" "$API_URL/health"

# Test data contract
test_endpoint "Data Contract" "$API_URL/contract"

# Test symbols
test_endpoint "Available Symbols" "$API_URL/symbols"

# Test timeframes
test_endpoint "Supported Timeframes" "$API_URL/timeframes"

# Test explain query
test_endpoint "Explain Query" "$API_URL/candles/explain?symbol=EURUSD&start=2024-01-01T00:00:00Z&end=2024-12-31T23:59:59Z"

# Test smart candles (if you have data)
echo "🔍 Testing Smart Candles Endpoint"
echo "================================="
echo ""
echo "This requires data in QuestDB. Testing with 1 month range..."
echo ""

end_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
start_date=$(date -u -d "30 days ago" +"%Y-%m-%dT%H:%M:%SZ")

test_endpoint "Smart Candles (30 days)" "$API_URL/candles/smart?symbol=EURUSD&start=$start_date&end=$end_date"

echo ""
echo "✅ Testing complete!"
echo ""
echo "📝 Notes:"
echo "- If candles endpoint fails, you may need to load data first"
echo "- Check the data contract for performance limits"
echo "- Use /candles/explain to understand query planning"