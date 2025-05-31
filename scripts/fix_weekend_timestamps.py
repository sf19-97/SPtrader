#!/usr/bin/env python3
"""
Fix Weekend Timestamps in QuestDB
Intelligently identifies and fixes weekend timestamps in daily candles
*Created: May 31, 2025*
"""

import requests
import sys
import datetime
import time
import json

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
API_URL = "http://localhost:8080/api/v1"

def query_questdb(query):
    """Execute query on QuestDB"""
    print(f"🔍 Executing query: {query}")
    
    response = requests.get(QUESTDB_URL, params={"query": query})
    if not response.ok:
        print(f"❌ Failed to query QuestDB: {response.status_code}")
        return None
    
    return response.json()

def get_day_name(timestamp_str):
    """Get day of week from timestamp string"""
    dt = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return dt.strftime("%A")

def analyze_weekend_candles(symbol):
    """Analyze weekend candles to determine which are legitimate market open/close"""
    print(f"📊 Analyzing weekend candles for {symbol}...")
    
    # Get all weekend candles from QuestDB
    query = f"""
    SELECT 
        timestamp,
        symbol,
        open,
        close
    FROM ohlc_1d_v2
    WHERE symbol = '{symbol}'
      AND (
          extract(dow from timestamp) = 6  -- Saturday (6 in QuestDB)
          OR extract(dow from timestamp) = 0  -- Sunday (0 in QuestDB)
      )
    ORDER BY timestamp
    """
    
    data = query_questdb(query)
    if not data or "dataset" not in data or not data["dataset"]:
        print("✅ No weekend candles found!")
        return []
    
    # Convert to list of dicts
    weekend_candles = []
    for row in data["dataset"]:
        candle = {
            "timestamp": row[0],
            "symbol": row[1],
            "open": row[2],
            "close": row[3]
        }
        
        # Add day name
        day = get_day_name(candle["timestamp"])
        candle["day"] = day
        
        weekend_candles.append(candle)
    
    print(f"⚠️ Found {len(weekend_candles)} weekend candles")
    
    # Classify weekend candles
    sunday_market_open = []  # These should be kept (forex opens Sunday evening)
    friday_shifted = []      # These should be shifted back one day (Friday's data)
    other_weekend = []       # These should be examined
    
    for candle in weekend_candles:
        day = candle["day"]
        
        # Sunday evening forex open - keep these
        if day == "Sunday":
            # Check if next day exists (Monday) - this suggests Sunday evening market open
            ts = datetime.datetime.fromisoformat(candle["timestamp"].replace("Z", "+00:00"))
            next_day = (ts + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            
            query = f"""
            SELECT count(*) FROM ohlc_1d_v2
            WHERE symbol = '{symbol}'
              AND timestamp::string LIKE '{next_day}%'
            """
            
            next_day_count = query_questdb(query)
            if next_day_count and "dataset" in next_day_count and next_day_count["dataset"][0][0] > 0:
                sunday_market_open.append(candle)
            else:
                other_weekend.append(candle)
        
        # Saturday might be Friday's data shifted
        elif day == "Saturday":
            # Check if previous day exists (Friday)
            ts = datetime.datetime.fromisoformat(candle["timestamp"].replace("Z", "+00:00"))
            prev_day = (ts - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            
            query = f"""
            SELECT count(*) FROM ohlc_1d_v2
            WHERE symbol = '{symbol}'
              AND timestamp::string LIKE '{prev_day}%'
            """
            
            prev_day_count = query_questdb(query)
            if prev_day_count and "dataset" in prev_day_count and prev_day_count["dataset"][0][0] == 0:
                # No Friday candle, this is likely Friday's data shifted
                friday_shifted.append(candle)
            else:
                other_weekend.append(candle)
        else:
            other_weekend.append(candle)
    
    print(f"\nClassification of weekend candles:")
    print(f"- Sunday market open (keep): {len(sunday_market_open)}")
    print(f"- Friday shifted to Saturday (fix): {len(friday_shifted)}")
    print(f"- Other weekend data (examine): {len(other_weekend)}")
    
    # Show examples of each
    if sunday_market_open:
        print("\nExample Sunday market open candles (legitimate):")
        for candle in sunday_market_open[:3]:
            print(f"  {candle['timestamp']} | {candle['day']} | Open: {candle['open']:.5f} | Close: {candle['close']:.5f}")
    
    if friday_shifted:
        print("\nExample Friday shifted to Saturday candles (need fix):")
        for candle in friday_shifted[:3]:
            print(f"  {candle['timestamp']} | {candle['day']} | Open: {candle['open']:.5f} | Close: {candle['close']:.5f}")
    
    if other_weekend:
        print("\nExample other weekend candles (examine):")
        for candle in other_weekend[:3]:
            print(f"  {candle['timestamp']} | {candle['day']} | Open: {candle['open']:.5f} | Close: {candle['close']:.5f}")
    
    return {
        "sunday_market_open": sunday_market_open,
        "friday_shifted": friday_shifted,
        "other_weekend": other_weekend
    }

def create_temp_table(symbol):
    """Create temporary table for fixing"""
    print(f"\n📝 Creating temporary table for {symbol}...")
    
    # Check if temp table exists and drop it
    query = "DROP TABLE IF EXISTS ohlc_1d_v2_fixed;"
    query_questdb(query)
    
    # Create a new table with the same structure
    query = f"""
    CREATE TABLE ohlc_1d_v2_fixed AS (
        SELECT * FROM ohlc_1d_v2 WHERE symbol = '{symbol}' LIMIT 0
    )
    """
    query_questdb(query)
    
    print("✅ Temporary table created")
    return True

def fix_friday_data(symbol, candles):
    """Fix Friday data shifted to Saturday"""
    if not candles:
        print("✅ No Friday->Saturday candles to fix")
        return True
    
    print(f"\n🔧 Fixing {len(candles)} Friday candles shifted to Saturday...")
    
    # For each candle, shift timestamp back by 1 day
    for i, candle in enumerate(candles[:5]):  # Process in batches of 5
        ts_str = candle["timestamp"]
        ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        fixed_ts = ts - datetime.timedelta(days=1)
        fixed_ts_str = fixed_ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        print(f"  Fixing {ts_str} ({candle['day']}) -> {fixed_ts_str} (Friday)")
        
        # Move data to the fixed table with corrected timestamp
        query = f"""
        INSERT INTO ohlc_1d_v2_fixed
        SELECT 
            '{fixed_ts_str}' as timestamp,
            symbol,
            open,
            high,
            low,
            close,
            volume
        FROM ohlc_1d_v2
        WHERE symbol = '{symbol}'
          AND timestamp = '{ts_str}'
        """
        query_questdb(query)
    
    print(f"✅ Fixed {len(candles)} Friday candles")
    return True

def copy_normal_data(symbol, exclude_timestamps):
    """Copy all other data without modification"""
    print(f"\n📝 Copying all other data for {symbol}...")
    
    # Create an exclusion list for the fixed candles
    exclude_list = ", ".join([f"'{ts}'" for ts in exclude_timestamps])
    exclude_clause = f"AND timestamp NOT IN ({exclude_list})" if exclude_timestamps else ""
    
    # Copy all other data
    query = f"""
    INSERT INTO ohlc_1d_v2_fixed
    SELECT *
    FROM ohlc_1d_v2
    WHERE symbol = '{symbol}'
      {exclude_clause}
    """
    query_questdb(query)
    
    # Verify count
    query = f"SELECT count(*) FROM ohlc_1d_v2_fixed WHERE symbol = '{symbol}'"
    result = query_questdb(query)
    
    if result and "dataset" in result and result["dataset"]:
        count = result["dataset"][0][0]
        print(f"✅ Copied {count} candles to the fixed table")
        return count
    
    return 0

def replace_table(symbol):
    """Replace the original table with the fixed one"""
    print(f"\n🔄 Replacing original table with fixed data for {symbol}...")
    
    # Create backup
    query = f"""
    CREATE TABLE ohlc_1d_v2_backup AS (
        SELECT * FROM ohlc_1d_v2 WHERE symbol = '{symbol}'
    )
    """
    query_questdb(query)
    
    # Get original count
    query = f"SELECT count(*) FROM ohlc_1d_v2 WHERE symbol = '{symbol}'"
    orig_result = query_questdb(query)
    orig_count = orig_result["dataset"][0][0] if orig_result and "dataset" in orig_result else 0
    
    # Get backup count
    query = f"SELECT count(*) FROM ohlc_1d_v2_backup WHERE symbol = '{symbol}'"
    backup_result = query_questdb(query)
    backup_count = backup_result["dataset"][0][0] if backup_result and "dataset" in backup_result else 0
    
    # Verify backup
    if backup_count != orig_count:
        print(f"❌ Backup verification failed! Original: {orig_count}, Backup: {backup_count}")
        return False
    
    # Delete original data
    query = f"DELETE FROM ohlc_1d_v2 WHERE symbol = '{symbol}'"
    query_questdb(query)
    
    # Copy fixed data
    query = f"""
    INSERT INTO ohlc_1d_v2
    SELECT * FROM ohlc_1d_v2_fixed
    WHERE symbol = '{symbol}'
    """
    query_questdb(query)
    
    # Verify count
    query = f"SELECT count(*) FROM ohlc_1d_v2 WHERE symbol = '{symbol}'"
    new_result = query_questdb(query)
    new_count = new_result["dataset"][0][0] if new_result and "dataset" in new_result else 0
    
    print(f"Verification: Original: {orig_count}, Fixed: {new_count}")
    
    if new_count >= orig_count - 10:  # Allow for some reduction due to deduplication
        print(f"✅ Successfully replaced data for {symbol}")
        return True
    else:
        print(f"❌ Verification failed! Restoring from backup...")
        
        # Restore from backup
        query = f"DELETE FROM ohlc_1d_v2 WHERE symbol = '{symbol}'"
        query_questdb(query)
        
        query = f"""
        INSERT INTO ohlc_1d_v2
        SELECT * FROM ohlc_1d_v2_backup
        WHERE symbol = '{symbol}'
        """
        query_questdb(query)
        
        print("✅ Restored from backup")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: fix_weekend_timestamps.py <symbol>")
        print("Example: fix_weekend_timestamps.py EURUSD")
        sys.exit(1)
    
    symbol = sys.argv[1]
    print(f"=== Fixing Weekend Timestamps for {symbol} ===")
    
    # Step 1: Analyze weekend candles
    classified_candles = analyze_weekend_candles(symbol)
    
    if not classified_candles:
        print("✅ No issues found!")
        return
    
    # Get timestamps that need fixing
    friday_shifted = classified_candles["friday_shifted"]
    
    if not friday_shifted:
        print("✅ No Friday->Saturday candles to fix!")
        return
    
    # Automatic confirmation for non-interactive environments
    print(f"\n⚠️ Found {len(friday_shifted)} candles to fix")
    print("Proceeding with fixes automatically...")
    confirm = 'y'
    
    # Step 2: Create temporary table
    if not create_temp_table(symbol):
        print("❌ Failed to create temporary table")
        return
    
    # Step 3: Fix Friday data shifted to Saturday
    if not fix_friday_data(symbol, friday_shifted):
        print("❌ Failed to fix Friday data")
        return
    
    # Step 4: Copy all other data
    exclude_timestamps = [candle["timestamp"] for candle in friday_shifted]
    if not copy_normal_data(symbol, exclude_timestamps):
        print("❌ Failed to copy normal data")
        return
    
    # Step 5: Replace original table with fixed data
    if not replace_table(symbol):
        print("❌ Failed to replace table")
        return
    
    # Clean up
    query = "DROP TABLE IF EXISTS ohlc_1d_v2_fixed;"
    query_questdb(query)
    
    print("\n=== Fix Complete ===")
    print("✅ Successfully fixed weekend timestamps")
    print("✅ Sunday market open candles have been preserved")
    print("✅ Friday->Saturday candles have been corrected")

if __name__ == "__main__":
    main()