#!/usr/bin/env python3
"""
Analyze Daily Candles
Examines daily candles to understand timestamp patterns
*Created: May 31, 2025*
"""

import requests
import sys
import datetime
import json

# Configuration
API_URL = "http://localhost:8080/api/v1"
QUESTDB_URL = "http://localhost:9000/exec"

def get_day_name(timestamp_str):
    """Get day of week from timestamp string"""
    dt = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return dt.strftime("%A")

def get_daily_candles_from_api(symbol, start, end):
    """Get daily candles from API"""
    print(f"📊 Getting daily candles from API for {symbol} ({start} to {end})...")
    
    url = f"{API_URL}/candles?symbol={symbol}&tf=1d&start={start}T00:00:00Z&end={end}T00:00:00Z"
    response = requests.get(url)
    
    if not response.ok:
        print(f"❌ Failed to get candles: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    if not data or "candles" not in data or not data["candles"]:
        print("❌ No candles returned")
        return []
    
    print(f"✅ Got {len(data['candles'])} daily candles from API")
    return data["candles"]

def query_questdb_directly(symbol, start, end):
    """Query QuestDB directly to check timestamps"""
    print(f"🔍 Querying QuestDB directly for {symbol} ({start} to {end})...")
    
    query = f"""
    SELECT 
        timestamp,
        symbol,
        open,
        close
    FROM ohlc_1d_v2
    WHERE symbol = '{symbol}'
      AND timestamp >= '{start}T00:00:00.000000Z'
      AND timestamp <= '{end}T00:00:00.000000Z'
    ORDER BY timestamp
    """
    
    response = requests.get(QUESTDB_URL, params={"query": query})
    if not response.ok:
        print(f"❌ Failed to query QuestDB: {response.status_code}")
        return []
    
    data = response.json()
    if "dataset" not in data:
        print("❌ No data returned from QuestDB")
        return []
    
    # Convert to list of dicts
    candles = []
    for row in data["dataset"]:
        candles.append({
            "timestamp": row[0],
            "symbol": row[1],
            "open": row[2],
            "close": row[3]
        })
    
    print(f"✅ Got {len(candles)} daily candles from QuestDB")
    return candles

def analyze_weekend_distribution(symbol, months=3):
    """Analyze the distribution of weekend timestamps across several months"""
    print(f"\n📊 Analyzing weekend distribution for {symbol} across {months} months...")
    
    # Check several months
    results = {}
    today = datetime.date.today()
    for i in range(months):
        month_date = today.replace(day=1) - datetime.timedelta(days=30*i)
        month_str = month_date.strftime("%Y-%m")
        start = month_date.replace(day=1).strftime("%Y-%m-%d")
        if month_date.month == 12:
            end = month_date.replace(year=month_date.year+1, month=1, day=1).strftime("%Y-%m-%d")
        else:
            end = month_date.replace(month=month_date.month+1, day=1).strftime("%Y-%m-%d")
        
        candles = get_daily_candles_from_api(symbol, start, end)
        
        # Count weekend days
        weekend_count = 0
        for candle in candles:
            day = get_day_name(candle["timestamp"])
            if day in ["Saturday", "Sunday"]:
                weekend_count += 1
        
        results[month_str] = {
            "total": len(candles),
            "weekend": weekend_count,
            "percentage": round(weekend_count / len(candles) * 100, 1) if candles else 0
        }
    
    print("\nWeekend distribution by month:")
    for month, data in results.items():
        print(f"  {month}: {data['weekend']}/{data['total']} weekend days ({data['percentage']}%)")
    
    return results

def check_march_2023_patterns(symbol):
    """Check specific patterns in March 2023"""
    print(f"\n🔎 Checking March 2023 patterns for {symbol}...")
    
    # Get candles from API
    candles = get_daily_candles_from_api(symbol, "2023-03-01", "2023-03-15")
    
    print("\nDaily candles in March 2023:")
    print("TIMESTAMP | DAY | OPEN | CLOSE | TRADING DAY?")
    print("-" * 70)
    
    # Analyze each candle
    weekday_with_weekend_timestamp = 0
    weekend_with_weekday_timestamp = 0
    
    for candle in candles:
        timestamp = candle["timestamp"]
        day = get_day_name(timestamp)
        
        # Determine if this is a legitimate trading day
        is_weekend = day in ["Saturday", "Sunday"]
        
        # Check for specific patterns
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        next_day = (dt + datetime.timedelta(days=1)).strftime("%A")
        prev_day = (dt - datetime.timedelta(days=1)).strftime("%A")
        
        if is_weekend and prev_day not in ["Saturday", "Sunday"]:
            # This might be Friday's data with Saturday timestamp
            weekday_with_weekend_timestamp += 1
            trading_day = f"YES (likely {prev_day}'s data)"
        elif not is_weekend and next_day not in ["Saturday", "Sunday"]:
            # This might be Sunday's data with Monday timestamp
            weekend_with_weekday_timestamp += 1
            trading_day = f"YES (likely {next_day}'s data)"
        else:
            trading_day = "YES" if not is_weekend else "NO"
        
        print(f"{timestamp} | {day} | {candle['open']:.5f} | {candle['close']:.5f} | {trading_day}")
    
    print(f"\nFound {weekday_with_weekend_timestamp} weekday candles with weekend timestamps")
    print(f"Found {weekend_with_weekday_timestamp} weekend candles with weekday timestamps")
    
    # Check QuestDB directly
    print("\nComparing with direct QuestDB query:")
    db_candles = query_questdb_directly(symbol, "2023-03-01", "2023-03-15")
    
    print("\nCandles in QuestDB:")
    print("TIMESTAMP | DAY | OPEN | CLOSE")
    print("-" * 60)
    
    for candle in db_candles:
        timestamp = candle["timestamp"]
        day = get_day_name(timestamp)
        is_weekend = day in ["Saturday", "Sunday"]
        weekend_marker = "⚠️ WEEKEND" if is_weekend else ""
        
        print(f"{timestamp} | {day} | {candle['open']:.5f} | {candle['close']:.5f} | {weekend_marker}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: analyze_daily_candles.py <symbol>")
        print("Example: analyze_daily_candles.py EURUSD")
        sys.exit(1)
    
    symbol = sys.argv[1]
    print(f"=== Analyzing Daily Candles for {symbol} ===")
    
    # Check March 2023 specifically
    check_march_2023_patterns(symbol)
    
    # Analyze weekend distribution
    analyze_weekend_distribution(symbol)
    
    print("\n=== Analysis Complete ===")

if __name__ == "__main__":
    main()