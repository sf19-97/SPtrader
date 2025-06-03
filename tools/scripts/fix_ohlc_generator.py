#!/usr/bin/env python3
"""
Fixed OHLC Generator with Date Range
Builds OHLC timeframes directly from tick data with specified date range
*Created: May 31, 2025*
"""

import requests
import sys
import time
import logging
from datetime import datetime, timedelta

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/fixed_ohlc_generator.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FixedOHLCGenerator")

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

def clear_ohlc_tables():
    """Clear all OHLC tables"""
    for timeframe in ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]:
        execute_query(f"DROP TABLE IF EXISTS ohlc_{timeframe}_v2")

def create_ohlc_tables():
    """Create OHLC tables for all timeframes"""
    for timeframe in ["1m", "5m", "15m", "30m", "1h", "4h"]:
        query = f"""
        CREATE TABLE IF NOT EXISTS ohlc_{timeframe}_v2 (
            timestamp TIMESTAMP,
            symbol SYMBOL,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume DOUBLE,
            tick_count LONG,
            vwap DOUBLE,
            trading_session SYMBOL,
            validation_status SYMBOL
        ) TIMESTAMP(timestamp) PARTITION BY DAY;
        """
        if not execute_query(query):
            logger.error(f"Failed to create ohlc_{timeframe}_v2 table")
            return False
    
    # Daily table with monthly partitioning
    query = """
    CREATE TABLE IF NOT EXISTS ohlc_1d_v2 (
        timestamp TIMESTAMP,
        symbol SYMBOL,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume DOUBLE,
        tick_count LONG,
        vwap DOUBLE,
        trading_session SYMBOL,
        validation_status SYMBOL
    ) TIMESTAMP(timestamp) PARTITION BY MONTH;
    """
    if not execute_query(query):
        logger.error("Failed to create ohlc_1d_v2 table")
        return False
    
    logger.info("✅ All OHLC tables created")
    return True

def generate_timeframe_candles(symbol, timeframe, start_date, end_date):
    """Generate candles for a specific timeframe"""
    logger.info(f"Generating {timeframe} candles for {symbol} from {start_date} to {end_date}")
    
    # Special handling for daily candles
    if timeframe == "1d":
        query = f"""
        INSERT INTO ohlc_{timeframe}_v2
        SELECT 
            timestamp::timestamp - 86400000000 as timestamp,  -- Shift back 1 day
            symbol,
            first(price) as open,
            max(price) as high,
            min(price) as low,
            last(price) as close,
            sum(volume) as volume,
            count() as tick_count,
            avg(price) as vwap,
            'MARKET' as trading_session,
            'VERIFIED' as validation_status
        FROM market_data_v2
        WHERE symbol = '{symbol}'
        AND timestamp >= '{start_date}'
        AND timestamp < '{end_date}'
        SAMPLE BY {timeframe} ALIGN TO CALENDAR
        """
    else:
        query = f"""
        INSERT INTO ohlc_{timeframe}_v2
        SELECT 
            timestamp,
            symbol,
            first(price) as open,
            max(price) as high,
            min(price) as low,
            last(price) as close,
            sum(volume) as volume,
            count() as tick_count,
            avg(price) as vwap,
            'MARKET' as trading_session,
            'VERIFIED' as validation_status
        FROM market_data_v2
        WHERE symbol = '{symbol}'
        AND timestamp >= '{start_date}'
        AND timestamp < '{end_date}'
        SAMPLE BY {timeframe} ALIGN TO CALENDAR
        """
    
    if not execute_query(query):
        logger.error(f"Failed to generate {timeframe} candles")
        return False
    
    # Count candles
    count_query = f"SELECT COUNT(*) FROM ohlc_{timeframe}_v2 WHERE symbol = '{symbol}'"
    result = execute_query(count_query)
    if result and 'dataset' in result and result['dataset']:
        count = result['dataset'][0][0]
        logger.info(f"Generated {count} {timeframe} candles")
    
    return True

def generate_all_timeframes(symbol, start_date, end_date):
    """Generate candles for all timeframes"""
    timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    success = True
    
    for timeframe in timeframes:
        if not generate_timeframe_candles(symbol, timeframe, start_date, end_date):
            logger.error(f"Failed to generate {timeframe} candles")
            success = False
            break
    
    if success:
        logger.info(f"✅ All timeframes generated for {symbol}")
    
    return success

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: fix_ohlc_generator.py <symbol> [<start_date> <end_date>]")
        print("Example: fix_ohlc_generator.py EURUSD 2023-03-01 2023-03-02")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    # Use command line dates or default to 1 day
    if len(sys.argv) >= 4:
        start_date = sys.argv[2]
        end_date = sys.argv[3]
    else:
        # Default to March 1, 2023
        start_date = "2023-03-01"
        end_date = "2023-03-02"
    
    # Ensure dates have proper format
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = start_dt.strftime("%Y-%m-%dT00:00:00.000000Z")
        end_date = end_dt.strftime("%Y-%m-%dT00:00:00.000000Z")
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    logger.info(f"=== Fixed OHLC Generation for {symbol} from {start_date} to {end_date} ===")
    
    try:
        # Verify database connection
        test_query = "SELECT 1"
        if not execute_query(test_query):
            logger.error("Failed to connect to QuestDB")
            sys.exit(1)
        
        # Verify tick data exists
        tick_query = f"""
        SELECT COUNT(*) 
        FROM market_data_v2 
        WHERE symbol = '{symbol}'
        AND timestamp >= '{start_date}'
        AND timestamp < '{end_date}'
        """
        result = execute_query(tick_query)
        
        if not result or 'dataset' not in result or not result['dataset']:
            logger.error(f"Failed to query tick data for {symbol}")
            sys.exit(1)
        
        tick_count = result['dataset'][0][0]
        logger.info(f"Found {tick_count:,} ticks for {symbol} in specified date range")
        
        if tick_count == 0:
            logger.error(f"No tick data found for {symbol} in specified date range")
            sys.exit(1)
        
        # Clear and recreate tables
        clear_ohlc_tables()
        if not create_ohlc_tables():
            logger.error("Failed to create OHLC tables")
            sys.exit(1)
        
        # Generate candles for all timeframes
        start_time = time.time()
        if generate_all_timeframes(symbol, start_date, end_date):
            elapsed_time = time.time() - start_time
            minutes, seconds = divmod(elapsed_time, 60)
            
            logger.info(f"=== OHLC Generation Complete ===")
            logger.info(f"Total processing time: {int(minutes)}m {int(seconds)}s")
            
            # Show summary of candles generated
            logger.info("=== OHLC Candle Summary ===")
            for tf in ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]:
                count_query = f"SELECT COUNT(*) FROM ohlc_{tf}_v2 WHERE symbol = '{symbol}'"
                result = execute_query(count_query, silent=True)
                if result and 'dataset' in result and result['dataset']:
                    count = result['dataset'][0][0]
                    logger.info(f"ohlc_{tf}_v2: {count:,} candles")
            
            # Show some sample candles
            for tf in ["1m", "5m", "1h", "1d"]:
                sample_query = f"""
                SELECT * FROM ohlc_{tf}_v2 
                WHERE symbol = '{symbol}'
                ORDER BY timestamp
                LIMIT 3
                """
                result = execute_query(sample_query, silent=True)
                if result and 'dataset' in result and result['dataset']:
                    logger.info(f"Sample {tf} candles:")
                    for row in result['dataset']:
                        logger.info(f"  {row}")
        else:
            logger.error("OHLC Generation failed")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error during OHLC generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()