#!/usr/bin/env python3
"""
Generate OHLC data for the full tick data range
*Created: May 27, 2025*
"""

import requests
import json
from datetime import datetime, timedelta

# QuestDB configuration
API_URL = "http://localhost:9000/exec"

def execute_query(query):
    """Execute a query against QuestDB"""
    response = requests.get(API_URL, params={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def generate_ohlc_for_range():
    """Generate OHLC data for all available tick data"""
    
    # Get the full data range
    print("Checking tick data range...")
    result = execute_query("""
        SELECT 
            symbol,
            min(timestamp) as start_date,
            max(timestamp) as end_date,
            count(*) as tick_count
        FROM market_data_v2
        GROUP BY symbol
    """)
    
    if not result or 'dataset' not in result:
        print("No tick data found")
        return
    
    print("\nAvailable tick data:")
    for row in result['dataset']:
        symbol = row[0]
        start = row[1]
        end = row[2]
        count = row[3]
        print(f"  {symbol}: {start} to {end} ({count:,} ticks)")
    
    # Generate OHLC for each symbol
    for row in result['dataset']:
        symbol = row[0]
        print(f"\nGenerating OHLC for {symbol}...")
        
        # Generate 1-minute OHLC
        print("  Generating 1-minute candles...")
        query = f"""
        INSERT INTO ohlc_1m_v2
        SELECT 
            DATE_TRUNC('minute', timestamp) as timestamp,
            '{symbol}' as symbol,
            FIRST(bid) as open,
            MAX(bid) as high,
            MIN(bid) as low,
            LAST(bid) as close,
            SUM(bid_volume) as volume
        FROM market_data_v2
        WHERE symbol = '{symbol}'
        GROUP BY DATE_TRUNC('minute', timestamp)
        """
        result = execute_query(query)
        if result:
            print(f"    ✓ Generated 1-minute candles")
        
        # Generate hourly OHLC
        print("  Generating 1-hour candles...")
        query = f"""
        INSERT INTO ohlc_1h_v2
        SELECT 
            DATE_TRUNC('hour', timestamp) as timestamp,
            '{symbol}' as symbol,
            FIRST(open) as open,
            MAX(high) as high,
            MIN(low) as low,
            LAST(close) as close,
            SUM(volume) as volume
        FROM ohlc_1m_v2
        WHERE symbol = '{symbol}'
        GROUP BY DATE_TRUNC('hour', timestamp)
        """
        result = execute_query(query)
        if result:
            print(f"    ✓ Generated 1-hour candles")
    
    # Check results
    print("\nVerifying OHLC generation...")
    for timeframe in ['1m', '1h']:
        result = execute_query(f"""
            SELECT 
                symbol,
                count(*) as candle_count,
                min(timestamp) as start,
                max(timestamp) as end
            FROM ohlc_{timeframe}_v2
            GROUP BY symbol
        """)
        
        if result and 'dataset' in result:
            print(f"\n{timeframe} candles:")
            for row in result['dataset']:
                print(f"  {row[0]}: {row[1]:,} candles ({row[2]} to {row[3]})")

if __name__ == "__main__":
    generate_ohlc_for_range()