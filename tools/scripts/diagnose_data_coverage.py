#!/usr/bin/env python3
"""
Diagnose data coverage issues across timeframes
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8080/api/v1"
QUESTDB_URL = "http://localhost:9000/exec"

def check_data_coverage():
    """Check data coverage to understand the structural issue"""
    
    print("🔍 DIAGNOSING DATA COVERAGE ISSUES")
    print("=" * 70)
    
    # Get overall data range
    response = requests.get(f"{API_BASE}/data/range?symbol=EURUSD")
    data_range = response.json()
    print(f"\n📊 Database Range: {data_range['start']} to {data_range['end']}")
    
    # Check monthly coverage
    print("\n📅 Monthly Data Coverage:")
    query = """
    SELECT 
      DATE_TRUNC('month', timestamp) as month,
      COUNT(*) as total_ticks,
      COUNT(DISTINCT DATE_TRUNC('day', timestamp)) as trading_days,
      MIN(timestamp) as first_tick,
      MAX(timestamp) as last_tick
    FROM market_data_v2
    WHERE symbol = 'EURUSD'
      AND timestamp >= '2024-01-01'
    GROUP BY month
    ORDER BY month DESC
    """
    
    response = requests.get(QUESTDB_URL, params={"query": query})
    if response.ok:
        data = response.json()
        print(f"{'Month':<20} {'Ticks':<12} {'Days':<6} {'Coverage'}")
        print("-" * 50)
        for row in data['dataset']:
            month = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
            ticks = row[1]
            days = row[2]
            first = row[3][:10]
            last = row[4][:10]
            print(f"{month.strftime('%B %Y'):<20} {ticks:<12,} {days:<6} {first} to {last}")
    
    # Check the last few days
    print("\n📆 Recent Daily Coverage:")
    query = """
    SELECT 
      DATE_TRUNC('day', timestamp) as day,
      COUNT(*) as ticks,
      MIN(EXTRACT(hour FROM timestamp)) as first_hour,
      MAX(EXTRACT(hour FROM timestamp)) as last_hour
    FROM market_data_v2
    WHERE symbol = 'EURUSD'
      AND timestamp >= '2024-02-20'
    GROUP BY day
    ORDER BY day DESC
    LIMIT 20
    """
    
    response = requests.get(QUESTDB_URL, params={"query": query})
    if response.ok:
        data = response.json()
        print(f"{'Date':<12} {'Ticks':<10} {'Hours':<12} {'Quality'}")
        print("-" * 45)
        for row in data['dataset']:
            day = row[0][:10]
            ticks = row[1]
            hours = f"{int(row[2]):02d}:00-{int(row[3]):02d}:59"
            quality = "GOOD" if ticks > 10000 else "POOR" if ticks > 1000 else "BAD"
            print(f"{day:<12} {ticks:<10,} {hours:<12} {quality}")
    
    # Test each timeframe
    print("\n🕐 Testing Each Timeframe:")
    timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    
    # Use a date we know has good data
    test_end = "2024-02-27T23:59:59Z"
    test_start = "2024-02-27T00:00:00Z"
    
    for tf in timeframes:
        params = {
            "symbol": "EURUSD",
            "tf": tf,
            "start": test_start,
            "end": test_end
        }
        response = requests.get(f"{API_BASE}/candles/native/v2", params=params)
        if response.ok:
            data = response.json()
            candles = data.get('candles', [])
            print(f"\n{tf:>3}: {len(candles)} candles for Feb 27")
            if candles:
                first = candles[0]['timestamp'][:16]
                last = candles[-1]['timestamp'][:16]
                print(f"     Range: {first} to {last}")

def find_structural_issue():
    """Identify the root cause of inconsistent loading"""
    
    print("\n\n🔧 STRUCTURAL ISSUES IDENTIFIED:")
    print("=" * 70)
    
    print("""
1. INCOMPLETE DATA MONTHS
   - March 2024 only has 5 days of data (ends March 5)
   - Some days have < 2k ticks (holidays/weekends/data issues)
   
2. INITIAL RANGE CALCULATION IS TOO SIMPLE
   - Always starts from the latest timestamp
   - Doesn't check if that period has good data
   - Different timeframes may land on different data quality days
   
3. NO DATA QUALITY VALIDATION
   - Frontend doesn't know which days have good/bad data
   - Can't intelligently skip bad periods
   
4. TIMEFRAME-SPECIFIC ISSUES
   - 5m chart: Shows only March 4 (because March 5 - 1 day = March 4)
   - 1h chart: May show more but include many gaps
   - Daily chart: Shows everything including bad data days
    """)
    
    print("\n💡 SOLUTIONS:")
    print("""
1. Add a data quality endpoint that returns good trading days
2. Update initial range logic to start from last good trading period
3. Implement intelligent date selection that skips bad data
4. Consider pre-computing data quality metrics in the database
    """)

if __name__ == "__main__":
    check_data_coverage()
    find_structural_issue()