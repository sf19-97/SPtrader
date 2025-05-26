#!/usr/bin/env python3
"""
Demo of lazy loading concept using existing API
*Created: May 25, 2025 22:57 UTC*
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8080/api/v1"

def check_current_data():
    """Check what data we currently have"""
    print("🔍 Checking current data availability...")
    
    # Test existing API
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        print("✅ API is healthy")
    
    # Try to get symbols
    try:
        response = requests.get(f"{API_BASE}/symbols")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available symbols: {len(data.get('symbols', []))}")
        else:
            print(f"❌ Failed to get symbols: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting symbols: {e}")

def test_data_query():
    """Test querying data we know exists"""
    print("\n📊 Testing data query for existing data...")
    
    # Query data for a range we know has data (Jan 2024)
    params = {
        "symbol": "EURUSD",
        "tf": "1h", 
        "start": "2024-01-19T10:00:00Z",
        "end": "2024-01-19T16:00:00Z"
    }
    
    try:
        response = requests.get(f"{API_BASE}/candles", params=params)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('data', []))
            print(f"✅ Retrieved {count} candles for existing data")
            if count > 0:
                first = data['data'][0]
                print(f"   First candle: {first['time']} O:{first['open']} H:{first['high']}")
        else:
            print(f"❌ Failed to get candles: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting candles: {e}")

def simulate_lazy_loading():
    """Simulate what lazy loading would do"""
    print("\n🔮 Simulating lazy loading behavior...")
    
    # Request data we probably don't have
    future_date = datetime(2024, 3, 1)  # March 1, 2024
    past_date = future_date - timedelta(days=7)
    
    print(f"📅 Requesting data for {past_date.date()} to {future_date.date()}")
    
    params = {
        "symbol": "GBPUSD",
        "tf": "1h",
        "start": past_date.isoformat() + "Z",
        "end": future_date.isoformat() + "Z"
    }
    
    try:
        response = requests.get(f"{API_BASE}/candles", params=params)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('data', []))
            print(f"📊 Found {count} candles for this period")
            if count == 0:
                print("💡 This is where lazy loading would kick in:")
                print("   1. Detect no data available")
                print("   2. Call dukascopy_to_ilp.py GBPUSD 2024-02-23 2024-03-01")
                print("   3. Load data via ILP")
                print("   4. Return data to user")
                print("   5. Future requests would be instant!")
        else:
            print(f"❌ Query failed: {response.status_code}")
            print("💡 Lazy loading would handle this by fetching the data")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_lazy_loading_workflow():
    """Show the conceptual workflow"""
    print("\n🏗️  Lazy Loading Workflow (When Implemented):")
    print("""
1. Frontend requests: GET /api/v1/candles/lazy?symbol=GBPUSD&tf=1h&start=...&end=...

2. API checks: Do we have this data?
   - Query QuestDB for tick data in this range
   - Identify any gaps

3. If gaps found:
   - Return HTTP 202 (Accepted) with message: "Fetching data..."
   - Background process calls: python3 dukascopy_to_ilp.py GBPUSD 2024-02-23 2024-03-01
   - Data gets loaded via ILP to QuestDB
   - OHLC candles generated

4. If data exists:
   - Return HTTP 200 with candles immediately
   - Super fast response from local QuestDB

5. Future requests:
   - All subsequent requests for this range are instant
   - No need to re-download from Dukascopy
    """)

def main():
    print("🚀 SPtrader Lazy Loading Demo")
    print("=" * 50)
    
    check_current_data()
    test_data_query()
    simulate_lazy_loading()
    show_lazy_loading_workflow()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Rebuild API binary to include lazy loading endpoints")
    print("2. Test /api/v1/data/check endpoint")
    print("3. Test /api/v1/data/ensure endpoint") 
    print("4. Test /api/v1/candles/lazy endpoint")
    print("5. Build React frontend that uses lazy loading")

if __name__ == "__main__":
    main()