#!/usr/bin/env python3
"""
OHLC Tables Purge Script
Drops all OHLC tables to prepare for complete rebuild
*Created: May 31, 2025*
"""

import requests
import logging
import sys

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/purge_ohlc_tables.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OHLCTablePurge")

def execute_query(query):
    """Execute a query against QuestDB with error handling"""
    logger.info(f"Executing query: {query}")
    
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
    logger.info("=== Starting OHLC tables purge ===")
    
    # List of tables to drop
    tables = ['ohlc_1m_v2', 'ohlc_5m_v2', 'ohlc_15m_v2', 'ohlc_30m_v2', 'ohlc_1h_v2', 'ohlc_4h_v2', 'ohlc_1d_v2']
    
    for table in tables:
        query = f"DROP TABLE IF EXISTS {table}"
        result = execute_query(query)
        if result:
            logger.info(f"✅ Table {table} dropped successfully")
        else:
            logger.error(f"❌ Failed to drop table {table}")
            sys.exit(1)
    
    logger.info("=== OHLC tables purge completed successfully ===")

if __name__ == "__main__":
    main()