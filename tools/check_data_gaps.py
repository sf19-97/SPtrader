#!/usr/bin/env python3
"""
Data Gap Detection Tool for SPtrader
Identifies missing data periods in market data
*Created: May 27, 2025*
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os
from collections import defaultdict

# Color class for terminal output
class Colors:
    YELLOW = '\033[93m'
    RESET = '\033[0m'

# Configuration
API_URL = "http://localhost:9000/exec"

def query_questdb(query):
    """Execute a query against QuestDB"""
    response = requests.get(API_URL, params={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def check_data_gaps(symbol=None):
    """Check for gaps in market data"""
    
    # Get all symbols if none specified
    if not symbol:
        result = query_questdb("SELECT DISTINCT symbol FROM market_data_v2 ORDER BY symbol")
        if not result or 'dataset' not in result:
            print("No data found in market_data_v2")
            return {}
        symbols = [row[0] for row in result['dataset']]
    else:
        symbols = [symbol]
    
    print("=" * 80)
    print("📊 SPtrader Data Gap Analysis")
    print("=" * 80)
    
    all_gaps = {}
    
    for sym in symbols:
        print(f"\n🔍 Analyzing {sym}...")
        
        # Get daily tick counts
        query = f"""
        SELECT 
            DATE_TRUNC('day', timestamp) as date,
            count(*) as tick_count,
            min(timestamp) as first_tick,
            max(timestamp) as last_tick
        FROM market_data_v2 
        WHERE symbol = '{sym}'
        GROUP BY date
        ORDER BY date
        """
        
        result = query_questdb(query)
        if not result or 'dataset' not in result or not result['dataset']:
            print(f"  ❌ No data found for {sym}")
            continue
        
        # Analyze gaps
        dates = []
        tick_counts = {}
        
        for row in result['dataset']:
            date = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
            dates.append(date)
            tick_counts[date] = row[1]
        
        # Check for missing days
        gaps = []
        if len(dates) > 1:
            current = dates[0]
            while current < dates[-1]:
                next_day = current + timedelta(days=1)
                # Skip weekends
                if next_day.weekday() < 5:  # Monday = 0, Friday = 4
                    if next_day not in tick_counts:
                        # Find the end of this gap
                        gap_start = next_day
                        gap_end = next_day
                        while gap_end < dates[-1] and gap_end not in tick_counts:
                            gap_end += timedelta(days=1)
                            if gap_end.weekday() >= 5:  # Skip weekends
                                gap_end += timedelta(days=2 if gap_end.weekday() == 5 else 1)
                        gaps.append((gap_start, gap_end - timedelta(days=1)))
                        current = gap_end
                    else:
                        current = next_day
                else:
                    current = next_day
        
        # Summary statistics
        total_days = len(dates)
        total_ticks = sum(tick_counts.values())
        avg_ticks = total_ticks / total_days if total_days > 0 else 0
        
        print(f"\n  📈 Summary for {sym}:")
        print(f"     Data range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
        print(f"     Total days: {total_days}")
        print(f"     Total ticks: {total_ticks:,}")
        print(f"     Average ticks/day: {avg_ticks:,.0f}")
        
        # Monthly breakdown
        print(f"\n  📅 Monthly breakdown:")
        query = f"""
        SELECT 
            DATE_TRUNC('month', timestamp) as month,
            count(*) as tick_count
        FROM market_data_v2 
        WHERE symbol = '{sym}'
        GROUP BY month
        ORDER BY month
        """
        
        result = query_questdb(query)
        if result and 'dataset' in result:
            for row in result['dataset']:
                month = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
                print(f"     {month.strftime('%B %Y')}: {row[1]:,} ticks")
        
        # Report gaps
        if gaps:
            print(f"\n  ⚠️  Data gaps found ({len(gaps)}):")
            for gap_start, gap_end in gaps:
                days = (gap_end - gap_start).days + 1
                if gap_start == gap_end:
                    print(f"     - {gap_start.strftime('%Y-%m-%d')} (1 day)")
                else:
                    print(f"     - {gap_start.strftime('%Y-%m-%d')} to {gap_end.strftime('%Y-%m-%d')} ({days} days)")
            all_gaps[sym] = gaps
        else:
            print(f"\n  ✅ No gaps found! Data is continuous.")
        
        # Check for low tick days (potential partial data)
        if avg_ticks > 0:
            low_tick_threshold = avg_ticks * 0.1  # Less than 10% of average
            low_days = [(date, count) for date, count in tick_counts.items() 
                       if count < low_tick_threshold and date.weekday() < 5]
            
            if low_days:
                print(f"\n  ⚠️  Days with unusually low tick counts:")
                for date, count in sorted(low_days)[:10]:  # Show max 10
                    print(f"     - {date.strftime('%Y-%m-%d')}: {count:,} ticks ({count/avg_ticks*100:.1f}% of average)")
    
    return all_gaps

def check_ohlc_gaps():
    """Check for gaps in OHLC data"""
    print("\n" + "=" * 80)
    print("📊 OHLC Data Coverage")
    print("=" * 80)
    
    tables = ['ohlc_1m_v2', 'ohlc_5m_v2', 'ohlc_15m_v2', 'ohlc_30m_v2', 
              'ohlc_1h_v2', 'ohlc_4h_v2', 'ohlc_1d_v2']
    
    for table in tables:
        query = f"""
        SELECT 
            symbol,
            count(*) as candle_count,
            min(timestamp) as start_date,
            max(timestamp) as end_date
        FROM {table}
        GROUP BY symbol
        ORDER BY symbol
        """
        
        result = query_questdb(query)
        if result and 'dataset' in result and result['dataset']:
            print(f"\n📊 {table}:")
            for row in result['dataset']:
                symbol = row[0]
                count = row[1]
                start = datetime.fromisoformat(row[2].replace('Z', '+00:00'))
                end = datetime.fromisoformat(row[3].replace('Z', '+00:00'))
                print(f"   {symbol}: {count:,} candles ({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')})")

def fill_gaps_interactive(gaps_by_symbol):
    """Interactively offer to fill detected gaps"""
    if not gaps_by_symbol:
        return
    
    print("\n" + "=" * 80)
    print("🔧 Gap Filling Options")
    print("=" * 80)
    
    # Count total gaps
    total_gaps = sum(len(gaps) for gaps in gaps_by_symbol.values())
    
    if total_gaps == 0:
        print("✅ No gaps to fill!")
        return
    
    print(f"\n⚠️  Found {total_gaps} gap(s) across {len(gaps_by_symbol)} symbol(s)")
    
    # Show summary
    for symbol, gaps in gaps_by_symbol.items():
        print(f"\n{symbol}:")
        for gap_start, gap_end in gaps:
            days = (gap_end - gap_start).days + 1
            print(f"  - {gap_start.strftime('%Y-%m-%d')} to {gap_end.strftime('%Y-%m-%d')} ({days} days)")
    
    # Ask if user wants to fill gaps
    print(f"\n{Colors.YELLOW}Would you like to fill these gaps? [y/N]: {Colors.RESET}", end='')
    sys.stdout.flush()
    
    try:
        response = input().strip().lower()
    except EOFError:
        # If no stdin available, default to no
        response = 'n'
    
    if response == 'y':
        print("\n🚀 Starting gap filling process...")
        
        for symbol, gaps in gaps_by_symbol.items():
            print(f"\n📊 Filling gaps for {symbol}...")
            
            for gap_start, gap_end in gaps:
                print(f"  Loading {gap_start.strftime('%Y-%m-%d')} to {gap_end.strftime('%Y-%m-%d')}...")
                
                # Use the batched loader
                cmd = f"cd /home/millet_frazier/SPtrader/data_feeds && python3 dukascopy_to_ilp_batched.py {symbol} {gap_start.strftime('%Y-%m-%d')} {gap_end.strftime('%Y-%m-%d')}"
                
                result = os.system(cmd)
                
                if result == 0:
                    print(f"  ✅ Successfully filled gap")
                else:
                    print(f"  ❌ Failed to fill gap (exit code: {result})")
        
        print("\n✅ Gap filling complete! Run the analysis again to verify.")
    else:
        print("\n📌 Gap filling skipped.")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check for data gaps in SPtrader market data')
    parser.add_argument('symbol', nargs='?', help='Symbol to check (e.g., EURUSD). If not specified, checks all symbols.')
    parser.add_argument('--ohlc', action='store_true', help='Also check OHLC data coverage')
    parser.add_argument('--fill', action='store_true', help='Offer to fill detected gaps')
    
    args = parser.parse_args()
    
    # Check if QuestDB is running
    try:
        response = requests.get(API_URL, params={'query': 'SELECT 1'}, timeout=2)
        if response.status_code != 200:
            print("❌ Error: QuestDB is not responding. Please start it with: sptrader start")
            sys.exit(1)
    except:
        print("❌ Error: Cannot connect to QuestDB. Please start it with: sptrader start")
        sys.exit(1)
    
    # Run gap analysis and collect gaps
    gaps_by_symbol = check_data_gaps(args.symbol)
    
    if args.ohlc:
        check_ohlc_gaps()
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    
    # Offer to fill gaps if requested
    if args.fill or (gaps_by_symbol and not args.ohlc):
        fill_gaps_interactive(gaps_by_symbol)

if __name__ == "__main__":
    main()