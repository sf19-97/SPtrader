#!/usr/bin/env python3
"""
Demonstrates lazy loading of forex data
*Created: May 25, 2025 21:20 UTC*
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8080/api/v1"

def check_data_availability(symbol, start, end):
    """Check what data we have for a symbol/range"""
    params = {
        "symbol": symbol,
        "start": start.isoformat() + "Z",
        "end": end.isoformat() + "Z"
    }
    
    response = requests.get(f"{API_BASE}/data/availability", params=params)
    return response.json()

def ensure_data(symbol, start, end):
    """Fetch missing data if needed"""
    data = {
        "symbol": symbol,
        "start": start.isoformat() + "Z",
        "end": end.isoformat() + "Z"
    }
    
    response = requests.post(f"{API_BASE}/data/ensure", json=data)
    return response.json()

def get_candles_lazy(symbol, timeframe, start, end):
    """Get candles with lazy loading"""
    params = {
        "symbol": symbol,
        "tf": timeframe,
        "start": start.isoformat() + "Z",
        "end": end.isoformat() + "Z"
    }
    
    response = requests.get(f"{API_BASE}/candles/lazy", params=params)
    return response.status_code, response.json()

def main():
    # Example: Request data we don't have yet
    symbol = "GBPUSD"
    end_date = datetime(2024, 2, 1)  # Feb 1, 2024
    start_date = end_date - timedelta(days=7)  # Jan 25, 2024
    
    print(f"🔍 Checking data availability for {symbol} from {start_date.date()} to {end_date.date()}")
    
    # Step 1: Check what data we have
    availability = check_data_availability(symbol, start_date, end_date)
    print(f"\nData availability: {json.dumps(availability, indent=2)}")
    
    if not availability.get("has_data") or availability.get("gaps"):
        print(f"\n📥 Data missing! Triggering fetch...")
        
        # Step 2: Request missing data
        fetch_result = ensure_data(symbol, start_date, end_date)
        print(f"Fetch initiated: {fetch_result}")
        
        # In a real app, you'd poll or wait for completion
        print("\n⏳ Data is being fetched in the background...")
        print("In production, you would:")
        print("1. Show a loading indicator")
        print("2. Poll /data/status endpoint")
        print("3. Or use WebSocket for real-time updates")
    
    # Step 3: Try to get candles (may return partial data)
    print(f"\n📊 Requesting candles...")
    status_code, candles_response = get_candles_lazy(symbol, "1h", start_date, end_date)
    
    if status_code == 200:
        print(f"✅ Full data available: {candles_response['count']} candles")
    elif status_code == 206:  # Partial Content
        print(f"⚠️  Partial data: {candles_response['count']} candles")
        print(f"Gaps: {candles_response.get('gaps', [])}")
    elif status_code == 202:  # Accepted
        print("📥 No data available, fetch needed")
        print(f"Message: {candles_response.get('message')}")

if __name__ == "__main__":
    main()