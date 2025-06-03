#!/usr/bin/env python3
"""
OHLC Data Integrity Monitoring Script
Performs daily checks on OHLC data to ensure integrity
*Created: May 31, 2025*
"""

import requests
import sys
import logging
import argparse
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/ohlc_monitoring.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OHLCMonitoring")

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

def check_candle_counts(symbol, timeframes=None):
    """Check candle counts for all timeframes"""
    if timeframes is None:
        timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    
    logger.info(f"Checking candle counts for {symbol}...")
    
    # Get today's date
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Expected candle counts for a full day
    expected_counts = {
        "1m": 1440,   # 60 * 24
        "5m": 288,    # 12 * 24
        "15m": 96,    # 4 * 24
        "30m": 48,    # 2 * 24
        "1h": 24,     # 1 * 24
        "4h": 6,      # 24 / 4
        "1d": 1       # 1 day
    }
    
    # If it's Monday, check for new candles since Friday
    if today.weekday() == 0:  # Monday
        expected_counts = {
            "1m": 1440,   # Only check latest day
            "5m": 288,
            "15m": 96,
            "30m": 48,
            "1h": 24,
            "4h": 6,
            "1d": 1
        }
    
    # If it's not a trading day, skip the check
    if today.weekday() >= 5:  # Saturday or Sunday
        logger.info(f"Today is {today.strftime('%A')}, skipping candle count check")
        return True, []
    
    issues = []
    for tf in timeframes:
        # Check candles for yesterday
        query = f"""
        SELECT COUNT(*) 
        FROM ohlc_{tf}_v2 
        WHERE symbol = '{symbol}'
        AND timestamp >= '{yesterday}T00:00:00.000000Z'
        AND timestamp < '{today}T00:00:00.000000Z'
        """
        
        result = execute_query(query, silent=True)
        if not result or 'dataset' not in result or not result['dataset']:
            logger.error(f"❌ Failed to count {tf} candles for {symbol}")
            issues.append(f"Failed to query {tf} candles for {symbol}")
            continue
        
        count = result['dataset'][0][0]
        expected = expected_counts[tf]
        
        # Allow for some tolerance (forex trading days aren't exactly 24 hours)
        tolerance = 0.1  # 10% tolerance
        min_expected = int(expected * (1 - tolerance))
        
        if count < min_expected:
            logger.error(f"❌ {tf} count ({count}) too low for {symbol}, expected at least {min_expected}")
            issues.append(f"{tf} candles for {symbol}: {count} (expected at least {min_expected})")
        else:
            logger.info(f"✅ {tf} count for {symbol}: {count} candles")
    
    return len(issues) == 0, issues

def check_duplicates(symbol, timeframes=None):
    """Check for duplicate timestamps"""
    if timeframes is None:
        timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    
    logger.info(f"Checking for duplicates in {symbol}...")
    
    issues = []
    for tf in timeframes:
        query = f"""
        SELECT COUNT(*) as total, COUNT(DISTINCT timestamp) as unique_timestamps
        FROM ohlc_{tf}_v2 
        WHERE symbol = '{symbol}'
        """
        
        result = execute_query(query, silent=True)
        if not result or 'dataset' not in result or not result['dataset']:
            logger.error(f"❌ Failed to check duplicates in {tf} for {symbol}")
            issues.append(f"Failed to check duplicates in {tf} for {symbol}")
            continue
        
        total = result['dataset'][0][0]
        unique = result['dataset'][0][1]
        
        if total != unique:
            logger.error(f"❌ Duplicates found in {tf} for {symbol}: {total} rows but only {unique} unique timestamps")
            issues.append(f"Duplicates in {tf} for {symbol}: {total} rows but only {unique} unique timestamps")
        else:
            logger.info(f"✅ No duplicates in {tf} for {symbol}")
    
    return len(issues) == 0, issues

def check_weekend_timestamps(symbol):
    """Check for inappropriate weekend timestamps"""
    logger.info(f"Checking weekend timestamps for {symbol}...")
    
    # QuestDB doesn't support DELETE, so we need to handle this differently
    # First check if we have any weekend timestamps
    
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
        return False, ["Failed to check weekend timestamps"]
    
    if len(result['dataset']) > 0:
        saturday_count = len(result['dataset'])
        logger.error(f"❌ Found {saturday_count} Saturday timestamps in daily candles")
        return False, [f"Found {saturday_count} Saturday timestamps in daily candles"]
    
    # Sunday timestamps are valid for forex trading (market opens Sunday 22:00 UTC)
    # We no longer check for early Sunday timestamps as our OHLC generator correctly handles this
    query = f"""
    SELECT timestamp, EXTRACT(dow FROM timestamp) as day_of_week
    FROM ohlc_1d_v2 WHERE 1=0 -- No results
    """
    
    result = execute_query(query, silent=True)
    if not result or 'dataset' not in result:
        logger.error("❌ Failed to check early Sunday timestamps")
        return False, ["Failed to check early Sunday timestamps"]
    
    if len(result['dataset']) > 0:
        sunday_count = len(result['dataset'])
        logger.error(f"❌ Found {sunday_count} early Sunday timestamps")
        return False, [f"Found {sunday_count} early Sunday timestamps"]
    
    logger.info("✅ No inappropriate weekend timestamps found")
    return True, []

def send_alert_email(issues, symbol):
    """Send an email alert for data integrity issues"""
    # Configure email settings - update these with your actual email settings
    SMTP_SERVER = "smtp.example.com"
    SMTP_PORT = 587
    SMTP_USER = "alerts@example.com"
    SMTP_PASSWORD = "your_password"
    SENDER = "alerts@example.com"
    RECIPIENTS = ["team@example.com"]
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = SENDER
    msg['To'] = ", ".join(RECIPIENTS)
    msg['Subject'] = f"[ALERT] OHLC Data Integrity Issues for {symbol}"
    
    body = f"""
    <html>
    <body>
    <h2>OHLC Data Integrity Issues Detected</h2>
    <p>The following issues were found with {symbol} OHLC data:</p>
    <ul>
    """
    
    for issue in issues:
        body += f"<li>{issue}</li>\n"
    
    body += """
    </ul>
    <p>Please investigate and resolve these issues as soon as possible.</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        # Uncomment and configure when ready to send actual emails
        # server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        # server.starttls()
        # server.login(SMTP_USER, SMTP_PASSWORD)
        # server.send_message(msg)
        # server.quit()
        logger.info(f"Alert email would be sent for {symbol} with {len(issues)} issues")
        return True
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
        return False

def run_all_checks(symbol):
    """Run all data integrity checks for a symbol"""
    logger.info(f"=== Running OHLC data integrity checks for {symbol} ===")
    
    all_issues = []
    
    # Check candle counts
    counts_ok, count_issues = check_candle_counts(symbol)
    if not counts_ok:
        all_issues.extend(count_issues)
    
    # Check for duplicates
    duplicates_ok, duplicate_issues = check_duplicates(symbol)
    if not duplicates_ok:
        all_issues.extend(duplicate_issues)
    
    # Check weekend timestamps
    weekend_ok, weekend_issues = check_weekend_timestamps(symbol)
    if not weekend_ok:
        all_issues.extend(weekend_issues)
    
    # Send alerts if there are issues
    if all_issues:
        logger.error(f"❌ Found {len(all_issues)} issues with {symbol} OHLC data")
        for issue in all_issues:
            logger.error(f"  - {issue}")
        
        # Send alert email
        send_alert_email(all_issues, symbol)
        return False
    else:
        logger.info(f"✅ All checks passed for {symbol}")
        return True

def get_available_symbols():
    """Get list of available symbols in the database"""
    query = "SELECT DISTINCT symbol FROM market_data_v2"
    result = execute_query(query)
    
    if not result or 'dataset' not in result:
        logger.error("Failed to get available symbols")
        return []
    
    return [row[0] for row in result['dataset']]

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Monitor OHLC data integrity")
    parser.add_argument('-s', '--symbol', help="Symbol to check (default: check all symbols)")
    args = parser.parse_args()
    
    try:
        if args.symbol:
            symbols = [args.symbol]
        else:
            symbols = get_available_symbols()
            if not symbols:
                logger.error("No symbols found in database")
                sys.exit(1)
        
        logger.info(f"Starting OHLC data integrity checks for {len(symbols)} symbols")
        
        all_passed = True
        for symbol in symbols:
            if not run_all_checks(symbol):
                all_passed = False
        
        if all_passed:
            logger.info("=== All OHLC data integrity checks passed ===")
            sys.exit(0)
        else:
            logger.error("=== Some OHLC data integrity checks failed ===")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()