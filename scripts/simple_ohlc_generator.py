#!/usr/bin/env python3
"""
Simple OHLC Generator
Builds OHLC timeframes using QuestDB's native sample by feature
*Created: May 31, 2025*
"""

import requests
import sys

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"

def execute_query(query):
    """Execute a query against QuestDB"""
    print(f"Executing: {query[:100]}..." if len(query) > 100 else f"Executing: {query}")
    
    response = requests.get(QUESTDB_URL, params={'query': query})
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    response_json = response.json()
    if 'error' in response_json:
        print(f"Error: {response_json['error']}")
        return False
    
    print("✅")
    return True

def build_15m_candles(symbol):
    """Build 15-minute candles from 1-minute data directly"""
    print(f"\n📈 Building 15-minute candles for {symbol}...")
    
    # Clear the existing data
    execute_query(f"DROP TABLE IF EXISTS ohlc_15m_v2_new")
    
    # Create the table with proper schema
    create_query = """
    CREATE TABLE ohlc_15m_v2_new (
        timestamp TIMESTAMP,
        symbol SYMBOL,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume DOUBLE,
        tick_count LONG,
        vwap DOUBLE,
        trading_session SYMBOL
    ) TIMESTAMP(timestamp) PARTITION BY DAY;
    """
    if not execute_query(create_query):
        return False
    
    # Insert data using direct sampling from 1-minute
    insert_query = f"""
    INSERT INTO ohlc_15m_v2_new
    SELECT 
        timestamp,
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        sum(tick_count) as tick_count,
        avg(vwap) as vwap,
        'AGGREGATED' as trading_session
    FROM ohlc_1m_v2
    WHERE symbol = '{symbol}'
    SAMPLE BY 15m ALIGN TO CALENDAR
    """
    if not execute_query(insert_query):
        return False
    
    # Swap tables
    execute_query("DROP TABLE IF EXISTS ohlc_15m_v2_old")
    execute_query("RENAME TABLE ohlc_15m_v2 TO ohlc_15m_v2_old")
    execute_query("RENAME TABLE ohlc_15m_v2_new TO ohlc_15m_v2")
    execute_query("DROP TABLE IF EXISTS ohlc_15m_v2_old")
    
    # Count the records
    count_query = f"SELECT COUNT(*) FROM ohlc_15m_v2 WHERE symbol = '{symbol}'"
    response = requests.get(QUESTDB_URL, params={'query': count_query})
    count = response.json()['dataset'][0][0] if 'dataset' in response.json() else 0
    
    print(f"✅ Created {count} 15-minute candles for {symbol}")
    return True

def build_30m_candles(symbol):
    """Build 30-minute candles from 1-minute data directly"""
    print(f"\n📈 Building 30-minute candles for {symbol}...")
    
    # Clear the existing data
    execute_query(f"DROP TABLE IF EXISTS ohlc_30m_v2_new")
    
    # Create the table with proper schema
    create_query = """
    CREATE TABLE ohlc_30m_v2_new (
        timestamp TIMESTAMP,
        symbol SYMBOL,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume DOUBLE,
        tick_count LONG,
        vwap DOUBLE,
        trading_session SYMBOL
    ) TIMESTAMP(timestamp) PARTITION BY DAY;
    """
    if not execute_query(create_query):
        return False
    
    # Insert data using direct sampling from 1-minute
    insert_query = f"""
    INSERT INTO ohlc_30m_v2_new
    SELECT 
        timestamp,
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        sum(tick_count) as tick_count,
        avg(vwap) as vwap,
        'AGGREGATED' as trading_session
    FROM ohlc_1m_v2
    WHERE symbol = '{symbol}'
    SAMPLE BY 30m ALIGN TO CALENDAR
    """
    if not execute_query(insert_query):
        return False
    
    # Swap tables
    execute_query("DROP TABLE IF EXISTS ohlc_30m_v2_old")
    execute_query("RENAME TABLE ohlc_30m_v2 TO ohlc_30m_v2_old")
    execute_query("RENAME TABLE ohlc_30m_v2_new TO ohlc_30m_v2")
    execute_query("DROP TABLE IF EXISTS ohlc_30m_v2_old")
    
    # Count the records
    count_query = f"SELECT COUNT(*) FROM ohlc_30m_v2 WHERE symbol = '{symbol}'"
    response = requests.get(QUESTDB_URL, params={'query': count_query})
    count = response.json()['dataset'][0][0] if 'dataset' in response.json() else 0
    
    print(f"✅ Created {count} 30-minute candles for {symbol}")
    return True

def build_1h_candles(symbol):
    """Build 1-hour candles from 1-minute data directly"""
    print(f"\n📈 Building 1-hour candles for {symbol}...")
    
    # Clear the existing data
    execute_query(f"DROP TABLE IF EXISTS ohlc_1h_v2_new")
    
    # Create the table with proper schema
    create_query = """
    CREATE TABLE ohlc_1h_v2_new (
        timestamp TIMESTAMP,
        symbol SYMBOL,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume DOUBLE,
        tick_count LONG,
        vwap DOUBLE,
        trading_session SYMBOL
    ) TIMESTAMP(timestamp) PARTITION BY DAY;
    """
    if not execute_query(create_query):
        return False
    
    # Insert data using direct sampling from 1-minute
    insert_query = f"""
    INSERT INTO ohlc_1h_v2_new
    SELECT 
        timestamp,
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        sum(tick_count) as tick_count,
        avg(vwap) as vwap,
        'AGGREGATED' as trading_session
    FROM ohlc_1m_v2
    WHERE symbol = '{symbol}'
    SAMPLE BY 1h ALIGN TO CALENDAR
    """
    if not execute_query(insert_query):
        return False
    
    # Swap tables
    execute_query("DROP TABLE IF EXISTS ohlc_1h_v2_old")
    execute_query("RENAME TABLE ohlc_1h_v2 TO ohlc_1h_v2_old")
    execute_query("RENAME TABLE ohlc_1h_v2_new TO ohlc_1h_v2")
    execute_query("DROP TABLE IF EXISTS ohlc_1h_v2_old")
    
    # Count the records
    count_query = f"SELECT COUNT(*) FROM ohlc_1h_v2 WHERE symbol = '{symbol}'"
    response = requests.get(QUESTDB_URL, params={'query': count_query})
    count = response.json()['dataset'][0][0] if 'dataset' in response.json() else 0
    
    print(f"✅ Created {count} 1-hour candles for {symbol}")
    return True

def build_4h_candles(symbol):
    """Build 4-hour candles from 1-minute data directly"""
    print(f"\n📈 Building 4-hour candles for {symbol}...")
    
    # Clear the existing data
    execute_query(f"DROP TABLE IF EXISTS ohlc_4h_v2_new")
    
    # Create the table with proper schema
    create_query = """
    CREATE TABLE ohlc_4h_v2_new (
        timestamp TIMESTAMP,
        symbol SYMBOL,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume DOUBLE,
        tick_count LONG,
        vwap DOUBLE,
        trading_session SYMBOL
    ) TIMESTAMP(timestamp) PARTITION BY DAY;
    """
    if not execute_query(create_query):
        return False
    
    # Insert data using direct sampling from 1-minute
    insert_query = f"""
    INSERT INTO ohlc_4h_v2_new
    SELECT 
        timestamp,
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        sum(tick_count) as tick_count,
        avg(vwap) as vwap,
        'AGGREGATED' as trading_session
    FROM ohlc_1m_v2
    WHERE symbol = '{symbol}'
    SAMPLE BY 4h ALIGN TO CALENDAR
    """
    if not execute_query(insert_query):
        return False
    
    # Swap tables
    execute_query("DROP TABLE IF EXISTS ohlc_4h_v2_old")
    execute_query("RENAME TABLE ohlc_4h_v2 TO ohlc_4h_v2_old")
    execute_query("RENAME TABLE ohlc_4h_v2_new TO ohlc_4h_v2")
    execute_query("DROP TABLE IF EXISTS ohlc_4h_v2_old")
    
    # Count the records
    count_query = f"SELECT COUNT(*) FROM ohlc_4h_v2 WHERE symbol = '{symbol}'"
    response = requests.get(QUESTDB_URL, params={'query': count_query})
    count = response.json()['dataset'][0][0] if 'dataset' in response.json() else 0
    
    print(f"✅ Created {count} 4-hour candles for {symbol}")
    return True

def build_1d_candles(symbol):
    """Build daily candles from 1-minute data directly"""
    print(f"\n📈 Building daily candles for {symbol}...")
    
    # Clear the existing data
    execute_query(f"DROP TABLE IF EXISTS ohlc_1d_v2_new")
    
    # Create the table with proper schema
    create_query = """
    CREATE TABLE ohlc_1d_v2_new (
        timestamp TIMESTAMP,
        symbol SYMBOL,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume DOUBLE,
        tick_count LONG,
        vwap DOUBLE,
        trading_session SYMBOL
    ) TIMESTAMP(timestamp) PARTITION BY MONTH;
    """
    if not execute_query(create_query):
        return False
    
    # Insert data using direct sampling from 1-minute
    insert_query = f"""
    INSERT INTO ohlc_1d_v2_new
    SELECT 
        timestamp,
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        sum(tick_count) as tick_count,
        avg(vwap) as vwap,
        'AGGREGATED' as trading_session
    FROM ohlc_1m_v2
    WHERE symbol = '{symbol}'
    SAMPLE BY 1d ALIGN TO CALENDAR
    """
    if not execute_query(insert_query):
        return False
    
    # Swap tables
    execute_query("DROP TABLE IF EXISTS ohlc_1d_v2_old")
    execute_query("RENAME TABLE ohlc_1d_v2 TO ohlc_1d_v2_old")
    execute_query("RENAME TABLE ohlc_1d_v2_new TO ohlc_1d_v2")
    execute_query("DROP TABLE IF EXISTS ohlc_1d_v2_old")
    
    # Count the records
    count_query = f"SELECT COUNT(*) FROM ohlc_1d_v2 WHERE symbol = '{symbol}'"
    response = requests.get(QUESTDB_URL, params={'query': count_query})
    count = response.json()['dataset'][0][0] if 'dataset' in response.json() else 0
    
    print(f"✅ Created {count} daily candles for {symbol}")
    return True

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python simple_ohlc_generator.py <symbol>")
        print("Example: python simple_ohlc_generator.py EURUSD")
        sys.exit(1)
    
    symbol = sys.argv[1]
    print(f"=== Generating OHLC timeframes for {symbol} ===")
    
    # Check if 1-minute data exists
    response = requests.get(QUESTDB_URL, params={'query': f"SELECT COUNT(*) FROM ohlc_1m_v2 WHERE symbol = '{symbol}'"})
    count = response.json()['dataset'][0][0] if 'dataset' in response.json() else 0
    
    if count == 0:
        print(f"❌ No 1-minute data found for {symbol}")
        sys.exit(1)
    
    print(f"Found {count} 1-minute candles for {symbol}")
    
    # Build each timeframe
    build_15m_candles(symbol)
    build_30m_candles(symbol)
    build_1h_candles(symbol)
    build_4h_candles(symbol)
    build_1d_candles(symbol)
    
    print("\n=== OHLC Generation Complete ===")
    print("\nCandle counts:")
    
    # Show final counts
    for table in ["ohlc_1m_v2", "ohlc_5m_v2", "ohlc_15m_v2", "ohlc_30m_v2", "ohlc_1h_v2", "ohlc_4h_v2", "ohlc_1d_v2"]:
        response = requests.get(QUESTDB_URL, params={'query': f"SELECT COUNT(*) FROM {table} WHERE symbol = '{symbol}'"})
        count = response.json()['dataset'][0][0] if 'dataset' in response.json() else 0
        print(f"  {table}: {count:,} candles")

if __name__ == "__main__":
    main()