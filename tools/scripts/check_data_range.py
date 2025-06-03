#!/usr/bin/env python3

import requests
import sys

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"

def execute_query(query):
    """Execute a query against QuestDB with error handling"""
    print(f"Executing query: {query}")
    
    try:
        response = requests.get(QUESTDB_URL, params={'query': query})
        if response.status_code != 200:
            print(f"Query failed with status {response.status_code}: {response.text}")
            return None
        
        result = response.json()
        if 'error' in result:
            print(f"Query error: {result['error']}")
            return None
        
        print("✅ Query executed successfully")
        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def main():
    symbol = "EURUSD"
    
    # Get date range
    query = f"SELECT min(timestamp), max(timestamp), count(*) FROM market_data_v2 WHERE symbol = '{symbol}'"
    result = execute_query(query)
    
    if result and 'dataset' in result and result['dataset']:
        min_date = result['dataset'][0][0]
        max_date = result['dataset'][0][1]
        count = result['dataset'][0][2]
        print(f"EURUSD data range: {min_date} to {max_date}, {count} records")
    
    # Test daily candle query
    query = f"""
    SELECT 
        timestamp,
        symbol,
        first(price) as open,
        max(price) as high,
        min(price) as low,
        last(price) as close,
        sum(volume) as volume,
        count() as tick_count,
        avg(price) as vwap
    FROM market_data_v2
    WHERE symbol = '{symbol}'
    AND timestamp >= '2023-03-01T00:00:00.000000Z'
    AND timestamp < '2023-03-10T00:00:00.000000Z'
    SAMPLE BY 1d ALIGN TO CALENDAR
    """
    result = execute_query(query)
    
    if result and 'dataset' in result and result['dataset']:
        print(f"Sample daily candles:")
        for row in result['dataset']:
            print(f"  {row}")
        print(f"Found {len(result['dataset'])} daily candles")

if __name__ == "__main__":
    main()