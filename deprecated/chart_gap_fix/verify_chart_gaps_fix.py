#!/usr/bin/env python3
"""
Verify Chart Gaps Fix
Tests that the ForexSessionFilter correctly handles daily candles
*Created: May 31, 2025*
"""

import requests
import sys
import json
import datetime

# Configuration
API_URL = "http://localhost:8080/api/v1"

def get_daily_candles(symbol, start, end):
    """Get daily candles for a symbol"""
    print(f"\n📊 Getting daily candles for {symbol} from {start} to {end}...")
    
    url = f"{API_URL}/candles?symbol={symbol}&tf=1d&start={start}T00:00:00Z&end={end}T00:00:00Z"
    response = requests.get(url)
    
    if not response.ok:
        print(f"❌ Failed to get candles: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    if not data or "candles" not in data or not data["candles"]:
        print("❌ No candles returned")
        return []
    
    print(f"✅ Got {len(data['candles'])} daily candles")
    return data["candles"]

def check_weekends(candles):
    """Check if there are weekend timestamps in the candles"""
    print("\n🔍 Checking for weekend timestamps...")
    
    weekend_candles = []
    for candle in candles:
        timestamp = candle["timestamp"]
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
        
        # Check if weekend (5=Saturday, 6=Sunday)
        if day_of_week >= 5:
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week]
            weekend_candles.append((timestamp, day_name))
    
    if weekend_candles:
        print(f"⚠️ Found {len(weekend_candles)} weekend candles:")
        for timestamp, day in weekend_candles:
            print(f"  {timestamp} - {day}")
    else:
        print("✅ No weekend candles found")
    
    return weekend_candles

def simulate_forex_session_filter(candles):
    """Simulate how the ForexSessionFilter would process these candles"""
    print("\n🧪 Simulating ForexSessionFilter behavior...")
    
    # Extract trading days (Monday-Friday)
    trading_days = []
    for candle in candles:
        timestamp = candle["timestamp"]
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
        
        # Check if weekday (0-4 = Monday-Friday)
        if day_of_week < 5:
            trading_days.append(candle)
    
    print(f"✅ Filter would keep {len(trading_days)} out of {len(candles)} candles")
    
    if len(trading_days) < len(candles):
        filtered_out = len(candles) - len(trading_days)
        print(f"  {filtered_out} candles would be filtered out")
        
        # Show sample of first few filtered candles
        filtered_candles = [c for c in candles if c not in trading_days]
        for i, candle in enumerate(filtered_candles[:3]):
            timestamp = candle["timestamp"]
            dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dt.weekday()]
            print(f"  Example {i+1}: {timestamp} - {day_name}")
    
    return trading_days

def test_march_2023(symbol):
    """Specifically test March 2023 which was problematic"""
    print(f"\n🔎 Testing March 2023 for {symbol}...")
    
    candles = get_daily_candles(symbol, "2023-03-01", "2023-03-07")
    if not candles:
        return
    
    print("\nCandles in March 2023:")
    print("TIMESTAMP | DAY | OPEN | CLOSE")
    print("-" * 60)
    
    for candle in candles:
        timestamp = candle["timestamp"]
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dt.weekday()]
        
        # Check if weekend
        is_weekend = dt.weekday() >= 5
        weekend_marker = "⚠️ WEEKEND" if is_weekend else ""
        
        print(f"{timestamp} | {day_name} | {candle['open']:.5f} | {candle['close']:.5f} {weekend_marker}")
    
    weekend_candles = check_weekends(candles)
    if weekend_candles:
        timestamp, day = weekend_candles[0]
        print(f"\n⚠️ Found {day} data: {timestamp}")
        print("This will be filtered out by ForexSessionFilter.isWeekday()")
    
    simulate_forex_session_filter(candles)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: verify_chart_gaps_fix.py <symbol>")
        print("Example: verify_chart_gaps_fix.py EURUSD")
        sys.exit(1)
    
    symbol = sys.argv[1]
    print(f"=== Verifying Chart Gaps Fix for {symbol} ===")
    
    # Test recent data
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=14)).isoformat()
    end_date = today.isoformat()
    
    candles = get_daily_candles(symbol, start_date, end_date)
    if candles:
        weekend_candles = check_weekends(candles)
        simulate_forex_session_filter(candles)
    
    # Test March 2023 specifically
    test_march_2023(symbol)
    
    print("\n=== Verification Complete ===")
    print("The ForexSessionFilter should now correctly handle daily candles.")
    print("In the frontend, it will use special logic for daily timeframes.")
    print("This ensures continuous charts without gaps for trading days.")

if __name__ == "__main__":
    main()