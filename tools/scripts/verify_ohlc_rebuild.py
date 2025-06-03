#!/usr/bin/env python3
"""
OHLC Rebuild Verification Script
Checks all symbol candle counts after the complete rebuild
*Created: May 31, 2025*
"""

import requests
import logging
import sys
from datetime import datetime

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/verify_ohlc_rebuild.log"

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

def execute_query(query):
    """Execute a query against QuestDB with error handling"""
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
        
        logger.info("✅ Query executed successfully")
        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return None

def main():
    logger.info("=== OHLC Rebuild Verification ===")
    
    # Get available symbols
    query = "SELECT DISTINCT symbol FROM market_data_v2"
    result = execute_query(query)
    if not result or 'dataset' not in result:
        logger.error("Failed to get available symbols")
        sys.exit(1)
    
    symbols = [row[0] for row in result['dataset']]
    logger.info(f"Found {len(symbols)} symbols: {', '.join(symbols)}")
    
    # Check candle counts for each timeframe
    timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    
    logger.info(f"\n=== CANDLE COUNT SUMMARY ===\n")
    logger.info(f"{'Symbol':<10} | {'1m':<10} | {'5m':<10} | {'15m':<10} | {'30m':<10} | {'1h':<10} | {'4h':<10} | {'1d':<10}")
    logger.info(f"{'-'*10:<10} | {'-'*10:<10} | {'-'*10:<10} | {'-'*10:<10} | {'-'*10:<10} | {'-'*10:<10} | {'-'*10:<10} | {'-'*10:<10}")
    
    for symbol in symbols:
        counts = {}
        for tf in timeframes:
            query = f"SELECT COUNT(*) FROM ohlc_{tf}_v2 WHERE symbol = '{symbol}'"
            result = execute_query(query)
            if result and 'dataset' in result and result['dataset']:
                counts[tf] = result['dataset'][0][0]
            else:
                counts[tf] = 0
        
        logger.info(f"{symbol:<10} | {counts['1m']:<10} | {counts['5m']:<10} | {counts['15m']:<10} | {counts['30m']:<10} | {counts['1h']:<10} | {counts['4h']:<10} | {counts['1d']:<10}")
    
    # Verify no duplicates exist
    logger.info(f"\n=== CHECKING FOR DUPLICATES ===\n")
    
    for symbol in symbols:
        for tf in timeframes:
            query = f"""
            SELECT COUNT(*) as total, COUNT(DISTINCT timestamp) as unique_timestamps
            FROM ohlc_{tf}_v2 
            WHERE symbol = '{symbol}'
            """
            result = execute_query(query)
            if result and 'dataset' in result and result['dataset']:
                total = result['dataset'][0][0]
                unique = result['dataset'][0][1]
                
                if total != unique:
                    logger.error(f"❌ Duplicates found in {tf} for {symbol}: {total} rows but only {unique} unique timestamps")
                else:
                    logger.info(f"✅ No duplicates in {tf} for {symbol}")
    
    # Verify no Saturday timestamps
    logger.info(f"\n=== CHECKING FOR WEEKEND TIMESTAMPS ===\n")
    
    for symbol in symbols:
        query = f"""
        SELECT COUNT(*)
        FROM ohlc_1d_v2
        WHERE symbol = '{symbol}'
        AND EXTRACT(dow FROM timestamp) = 6  -- Saturday
        """
        result = execute_query(query)
        if result and 'dataset' in result and result['dataset']:
            count = result['dataset'][0][0]
            if count > 0:
                logger.error(f"❌ Found {count} Saturday timestamps for {symbol}")
            else:
                logger.info(f"✅ No Saturday timestamps found for {symbol}")
    
    logger.info("=== OHLC Rebuild Verification Complete ===")

if __name__ == "__main__":
    main()