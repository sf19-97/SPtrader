#!/usr/bin/env python3
"""
Test Script - Generate OHLC for Small Timeframe
Tests OHLC generation with a small time range (1 hour)
*Created: May 31, 2025*
"""

import requests
import sys
import time
import logging
from datetime import datetime

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/test_small_timeframe.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestSmallTimeframe")

def execute_query(query, silent=False):
    """Execute a query against QuestDB with error handling"""
    if not silent:
        logger.info(f"Executing query: {query[:100]}..." if len(query) > 100 else f"Executing query: {query}")
    
    try:
        response = requests.get(QUESTDB_URL, params={'query': query})
        if response.status_code != 200:
            logger.error(f"Query failed with status {response.status_code}: {response.text}")
            return None
        
        result = response.json()
        if 'error' in result:
            logger.error(f"Query error: {result['error']}")
            return None
        
        if not silent:
            logger.info("✅ Query executed successfully")
        
        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return None

def clear_test_tables():
    """Clear all test tables"""
    tables = ["test_1m", "test_5m", "test_15m", "test_1h"]
    for table in tables:
        execute_query(f"DROP TABLE IF EXISTS {table}")

def create_test_tables():
    """Create test tables for OHLC data"""
    for timeframe in ["1m", "5m", "15m", "1h"]:
        query = f"""
        CREATE TABLE IF NOT EXISTS test_{timeframe} (
            timestamp TIMESTAMP,
            symbol SYMBOL,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume DOUBLE,
            tick_count LONG
        ) TIMESTAMP(timestamp);
        """
        if not execute_query(query):
            logger.error(f"Failed to create test_{timeframe} table")
            return False
    
    return True

def generate_test_candles(symbol, start_date, end_date):
    """Generate test candles for a specific timeframe"""
    
    # Generate 1-minute candles
    timeframe = "1m"
    logger.info(f"Generating {timeframe} candles for {symbol} from {start_date} to {end_date}")
    
    query = f"""
    INSERT INTO test_{timeframe}
    SELECT 
        timestamp,
        symbol,
        first(price) as open,
        max(price) as high,
        min(price) as low,
        last(price) as close,
        sum(volume) as volume,
        count() as tick_count
    FROM market_data_v2
    WHERE symbol = '{symbol}'
    AND timestamp >= '{start_date}'
    AND timestamp < '{end_date}'
    SAMPLE BY {timeframe}
    """
    
    if not execute_query(query):
        logger.error(f"Failed to generate {timeframe} candles")
        return False
    
    # Count candles
    count_query = f"SELECT COUNT(*) FROM test_{timeframe}"
    result = execute_query(count_query)
    if result and 'dataset' in result and result['dataset']:
        count = result['dataset'][0][0]
        logger.info(f"Generated {count} {timeframe} candles")
    
    # Generate 5-minute candles
    timeframe = "5m"
    logger.info(f"Generating {timeframe} candles for {symbol} from {start_date} to {end_date}")
    
    query = f"""
    INSERT INTO test_{timeframe}
    SELECT 
        timestamp,
        symbol,
        first(price) as open,
        max(price) as high,
        min(price) as low,
        last(price) as close,
        sum(volume) as volume,
        count() as tick_count
    FROM market_data_v2
    WHERE symbol = '{symbol}'
    AND timestamp >= '{start_date}'
    AND timestamp < '{end_date}'
    SAMPLE BY {timeframe}
    """
    
    if not execute_query(query):
        logger.error(f"Failed to generate {timeframe} candles")
        return False
    
    # Count candles
    count_query = f"SELECT COUNT(*) FROM test_{timeframe}"
    result = execute_query(count_query)
    if result and 'dataset' in result and result['dataset']:
        count = result['dataset'][0][0]
        logger.info(f"Generated {count} {timeframe} candles")
    
    # Generate 1-hour candles
    timeframe = "1h"
    logger.info(f"Generating {timeframe} candles for {symbol} from {start_date} to {end_date}")
    
    query = f"""
    INSERT INTO test_{timeframe}
    SELECT 
        timestamp,
        symbol,
        first(price) as open,
        max(price) as high,
        min(price) as low,
        last(price) as close,
        sum(volume) as volume,
        count() as tick_count
    FROM market_data_v2
    WHERE symbol = '{symbol}'
    AND timestamp >= '{start_date}'
    AND timestamp < '{end_date}'
    SAMPLE BY {timeframe}
    """
    
    if not execute_query(query):
        logger.error(f"Failed to generate {timeframe} candles")
        return False
    
    # Count candles
    count_query = f"SELECT COUNT(*) FROM test_{timeframe}"
    result = execute_query(count_query)
    if result and 'dataset' in result and result['dataset']:
        count = result['dataset'][0][0]
        logger.info(f"Generated {count} {timeframe} candles")
    
    # Show sample candles
    for timeframe in ["1m", "5m", "1h"]:
        sample_query = f"SELECT * FROM test_{timeframe} ORDER BY timestamp LIMIT 3"
        result = execute_query(sample_query, silent=True)
        if result and 'dataset' in result and result['dataset']:
            logger.info(f"Sample {timeframe} candles:")
            for row in result['dataset']:
                logger.info(f"  {row}")
    
    return True

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: test_small_timeframe.py <symbol>")
        print("Example: test_small_timeframe.py EURUSD")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    # Use a small timeframe for testing
    start_date = "2023-03-01T10:00:00.000000Z"
    end_date = "2023-03-01T11:00:00.000000Z"
    
    logger.info(f"=== Testing OHLC Generation for {symbol} from {start_date} to {end_date} ===")
    
    try:
        # Clear existing test tables
        clear_test_tables()
        
        # Create new test tables
        if not create_test_tables():
            logger.error("Failed to create test tables")
            sys.exit(1)
        
        # Generate candles
        start_time = time.time()
        if generate_test_candles(symbol, start_date, end_date):
            elapsed_time = time.time() - start_time
            logger.info(f"=== Test completed in {elapsed_time:.2f} seconds ===")
            
            # Show final counts
            for timeframe in ["1m", "5m", "1h"]:
                count_query = f"SELECT COUNT(*) FROM test_{timeframe}"
                result = execute_query(count_query, silent=True)
                if result and 'dataset' in result and result['dataset']:
                    count = result['dataset'][0][0]
                    logger.info(f"test_{timeframe}: {count} candles")
        else:
            logger.error("Test failed")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error during test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()