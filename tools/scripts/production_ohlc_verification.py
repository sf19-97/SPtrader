#!/usr/bin/env python3
"""
Production OHLC Verification Script
Validates OHLC data integrity after generation
*Created: May 31, 2025*
"""

import requests
import sys
import logging
from datetime import datetime, timedelta

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/ohlc_verification.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OHLCVerification")

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

def verify_candle_counts(symbol):
    """Verify candle counts for all timeframes"""
    logger.info(f"Verifying candle counts for {symbol}...")
    
    timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    counts = {}
    
    for tf in timeframes:
        query = f"SELECT COUNT(*) FROM ohlc_{tf}_v2 WHERE symbol = '{symbol}'"
        result = execute_query(query, silent=True)
        
        if not result or 'dataset' not in result or not result['dataset']:
            logger.error(f"❌ Failed to count {tf} candles")
            return False
        
        count = result['dataset'][0][0]
        counts[tf] = count
        
        if count == 0:
            logger.error(f"❌ No candles found for {tf}")
            return False
    
    # Verify count ratios (approximately)
    if counts["1m"] < counts["5m"] * 4.5:
        logger.error(f"❌ 1m count ({counts['1m']}) too low compared to 5m count ({counts['5m']})")
        return False
    
    if counts["5m"] < counts["15m"] * 2.5:
        logger.error(f"❌ 5m count ({counts['5m']}) too low compared to 15m count ({counts['15m']})")
        return False
    
    if counts["15m"] < counts["30m"] * 1.5:
        logger.error(f"❌ 15m count ({counts['15m']}) too low compared to 30m count ({counts['30m']})")
        return False
    
    if counts["30m"] < counts["1h"] * 1.5:
        logger.error(f"❌ 30m count ({counts['30m']}) too low compared to 1h count ({counts['1h']})")
        return False
    
    if counts["1h"] < counts["4h"] * 3.5:
        logger.error(f"❌ 1h count ({counts['1h']}) too low compared to 4h count ({counts['4h']})")
        return False
    
    if counts["4h"] < counts["1d"] * 3.5:
        logger.error(f"❌ 4h count ({counts['4h']}) too low compared to 1d count ({counts['1d']})")
        return False
    
    logger.info("Candle counts by timeframe:")
    for tf in timeframes:
        logger.info(f"  {tf}: {counts[tf]:,} candles")
    
    return True

def verify_no_duplicates(symbol):
    """Verify no duplicate timestamps in any timeframe"""
    logger.info(f"Verifying no duplicates for {symbol}...")
    
    timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    all_valid = True
    
    for tf in timeframes:
        # Count total rows
        count_query = f"SELECT COUNT(*) FROM ohlc_{tf}_v2 WHERE symbol = '{symbol}'"
        count_result = execute_query(count_query, silent=True)
        
        if not count_result or 'dataset' not in count_result or not count_result['dataset']:
            logger.error(f"❌ Failed to count rows in {tf}")
            all_valid = False
            continue
        
        total_rows = count_result['dataset'][0][0]
        
        # Count distinct timestamps
        distinct_query = f"SELECT COUNT(DISTINCT timestamp) FROM ohlc_{tf}_v2 WHERE symbol = '{symbol}'"
        distinct_result = execute_query(distinct_query, silent=True)
        
        if not distinct_result or 'dataset' not in distinct_result or not distinct_result['dataset']:
            logger.error(f"❌ Failed to count distinct timestamps in {tf}")
            all_valid = False
            continue
        
        distinct_timestamps = distinct_result['dataset'][0][0]
        
        if total_rows != distinct_timestamps:
            logger.error(f"❌ Duplicates found in {tf}: {total_rows} rows but only {distinct_timestamps} unique timestamps")
            all_valid = False
        else:
            logger.info(f"✅ No duplicates in {tf} ({distinct_timestamps} unique timestamps)")
    
    return all_valid

def verify_weekend_timestamps(symbol):
    """Verify no inappropriate weekend timestamps exist"""
    logger.info(f"Verifying weekend timestamps for {symbol}...")
    
    # Check for Saturday timestamps in daily candles
    query = f"""
    SELECT timestamp, EXTRACT(dow FROM timestamp) as day_of_week
    FROM ohlc_1d_v2
    WHERE symbol = '{symbol}'
    AND EXTRACT(dow FROM timestamp) = 6  -- Saturday
    """
    
    result = execute_query(query, silent=True)
    if not result or 'dataset' not in result:
        logger.error("❌ Failed to check weekend timestamps")
        return False
    
    if len(result['dataset']) > 0:
        logger.error(f"❌ Found {len(result['dataset'])} Saturday timestamps")
        for row in result['dataset']:
            logger.error(f"  - Saturday timestamp: {row[0]}")
        return False
    
    # Check for early Sunday timestamps in daily candles
    query = f"""
    SELECT timestamp, EXTRACT(dow FROM timestamp) as day_of_week
    FROM ohlc_1d_v2
    WHERE symbol = '{symbol}'
    AND EXTRACT(dow FROM timestamp) = 0  -- Sunday
    AND EXTRACT(hour FROM timestamp) < 22  -- Before 22:00 UTC (typical market open)
    """
    
    result = execute_query(query, silent=True)
    if not result or 'dataset' not in result:
        logger.error("❌ Failed to check early Sunday timestamps")
        return False
    
    if len(result['dataset']) > 0:
        logger.error(f"❌ Found {len(result['dataset'])} early Sunday timestamps")
        for row in result['dataset']:
            logger.error(f"  - Early Sunday timestamp: {row[0]}")
        return False
    
    logger.info("✅ No inappropriate weekend timestamps found")
    return True

def verify_price_continuity(symbol):
    """Verify price continuity between candles"""
    logger.info(f"Verifying price continuity for {symbol}...")
    
    # Check price continuity in 1-hour candles
    query = f"""
    SELECT 
        timestamp, 
        close,
        lead(open) OVER (ORDER BY timestamp) AS next_open,
        abs(close - lead(open) OVER (ORDER BY timestamp)) AS price_gap
    FROM ohlc_1h_v2
    WHERE symbol = '{symbol}'
    ORDER BY timestamp
    """
    
    result = execute_query(query, silent=True)
    if not result or 'dataset' not in result:
        logger.error("❌ Failed to check price continuity")
        return False
    
    large_gaps = 0
    for row in result['dataset']:
        if len(row) >= 4 and row[3] is not None and row[3] > 0.0010:  # 10 pips gap
            large_gaps += 1
            logger.warning(f"⚠️ Large price gap of {row[3]:.5f} at {row[0]}")
    
    if large_gaps > 0:
        logger.warning(f"⚠️ Found {large_gaps} large price gaps")
    else:
        logger.info("✅ Price continuity verified")
    
    # Still pass the check, but with a warning
    return True

def verify_tick_coverage(symbol):
    """Verify candles have reasonable tick coverage"""
    logger.info(f"Verifying tick coverage for {symbol}...")
    
    # Check for suspiciously low tick counts
    query = f"""
    SELECT timestamp, tick_count, high, low, high - low AS range
    FROM ohlc_1m_v2
    WHERE symbol = '{symbol}'
    AND tick_count < 5
    AND high - low > 0.0010  -- 10 pips range
    LIMIT 10
    """
    
    result = execute_query(query, silent=True)
    if not result or 'dataset' not in result:
        logger.error("❌ Failed to check tick coverage")
        return False
    
    if len(result['dataset']) > 0:
        logger.warning(f"⚠️ Found {len(result['dataset'])} candles with suspicious tick coverage")
        for row in result['dataset']:
            logger.warning(f"  - Suspicious candle at {row[0]}: tick_count={row[1]} but range={row[4]:.5f}")
    else:
        logger.info("✅ Tick coverage verified")
    
    # Still pass the check, but with a warning
    return True

def verify_ohlc_data(symbol):
    """Run all verification checks for a symbol"""
    logger.info(f"=== Verifying OHLC data for {symbol} ===")
    
    checks = [
        verify_candle_counts(symbol),
        verify_no_duplicates(symbol),
        verify_weekend_timestamps(symbol),
        verify_price_continuity(symbol),
        verify_tick_coverage(symbol)
    ]
    
    if all(checks):
        logger.info(f"✅ All verification checks passed for {symbol}")
        return True
    else:
        logger.error(f"❌ Some verification checks failed for {symbol}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: production_ohlc_verification.py <symbol>")
        print("Example: production_ohlc_verification.py EURUSD")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    try:
        # Run all verification checks
        if verify_ohlc_data(symbol):
            logger.info(f"=== OHLC data verified for {symbol} ===")
            print(f"✅ OHLC data verified for {symbol}")
            sys.exit(0)
        else:
            logger.error(f"=== OHLC data verification failed for {symbol} ===")
            print(f"❌ OHLC data verification failed for {symbol}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()