#!/usr/bin/env python3
# Data Gap Analysis Tool
# Detects missing tick data in market_data_v2 table
# Created: May 31, 2025

import argparse
import datetime
import sys
import psycopg2
import psycopg2.extras
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate
from dateutil.relativedelta import relativedelta

# Database connection parameters
DB_PARAMS = {
    "dbname": "qdb",
    "user": "admin",
    "password": "quest",
    "host": "localhost",
    "port": 8812
}

def connect_to_db():
    """Connect to QuestDB database"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def get_data_coverage(conn, symbol, start_date, end_date, interval='1d'):
    """
    Analyze data coverage for a symbol between start and end dates
    Returns a list of dates and their tick counts
    """
    cursor = conn.cursor()
    
    # Convert dates to datetime objects if they're strings
    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Generate intervals based on requested interval
    intervals = []
    current_date = start_date
    
    if interval == '1d':
        while current_date <= end_date:
            intervals.append(current_date)
            current_date += datetime.timedelta(days=1)
    elif interval == '1w':
        # Start from Monday of the week containing start_date
        monday = start_date - datetime.timedelta(days=start_date.weekday())
        current_date = monday
        while current_date <= end_date:
            intervals.append(current_date)
            current_date += datetime.timedelta(days=7)
    elif interval == '1M':
        # Start from first day of the month containing start_date
        current_date = datetime.date(start_date.year, start_date.month, 1)
        while current_date <= end_date:
            intervals.append(current_date)
            current_date += relativedelta(months=1)
    
    # Query to get tick counts for each interval
    results = []
    
    for i in range(len(intervals) - 1):
        interval_start = intervals[i]
        interval_end = intervals[i+1]
        
        query = f"""
        SELECT COUNT(*) 
        FROM market_data_v2 
        WHERE symbol = '{symbol}' 
        AND timestamp >= '{interval_start}' 
        AND timestamp < '{interval_end}'
        """
        
        cursor.execute(query)
        count = cursor.fetchone()[0]
        results.append((interval_start, count))
    
    cursor.close()
    return results

def identify_data_gaps(coverage_data, threshold=500):
    """
    Identify periods with missing or insufficient data
    Returns periods with tick count below threshold
    """
    gaps = []
    for date, count in coverage_data:
        # Skip weekends (Saturday and Sunday)
        weekday = date.weekday()
        if weekday == 5 or weekday == 6:  # 5=Saturday, 6=Sunday
            continue
            
        if count < threshold:
            gaps.append((date, count))
    
    return gaps

def visualize_coverage(coverage_data, symbol, interval='1d'):
    """Create a visualization of data coverage"""
    dates = [item[0] for item in coverage_data]
    counts = [item[1] for item in coverage_data]
    
    # Create a figure
    plt.figure(figsize=(12, 6))
    
    # Create a bar chart
    bars = plt.bar(dates, counts)
    
    # Color bars based on tick count (red for gaps)
    for i, bar in enumerate(bars):
        if coverage_data[i][1] < 500:
            bar.set_color('red')
        else:
            bar.set_color('green')
    
    # Format the plot
    plt.title(f'Tick Data Coverage for {symbol} ({interval})')
    plt.xlabel('Date')
    plt.ylabel('Number of Ticks')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the figure
    output_file = f"{symbol}_coverage_{interval}.png"
    plt.savefig(output_file)
    print(f"Coverage visualization saved to {output_file}")

def print_table(data, headers, title=None):
    """Print data in a formatted table"""
    if title:
        print(f"\n{title}")
    print(tabulate(data, headers=headers, tablefmt="grid"))

def suggest_loading_command(symbol, gaps):
    """Suggest commands to load missing data"""
    if not gaps:
        return
    
    print("\nSuggested commands to fill data gaps:")
    
    # Group consecutive dates
    groups = []
    current_group = [gaps[0][0]]
    
    for i in range(1, len(gaps)):
        prev_date = gaps[i-1][0]
        curr_date = gaps[i][0]
        
        # If dates are consecutive, add to current group
        if (curr_date - prev_date).days == 1:
            current_group.append(curr_date)
        else:
            # Finish current group and start a new one
            groups.append(current_group)
            current_group = [curr_date]
    
    # Add the last group
    if current_group:
        groups.append(current_group)
    
    # Generate commands for each group
    for group in groups:
        start_date = group[0]
        end_date = group[-1]
        
        # Add a day to end_date to include it in the range
        end_date += datetime.timedelta(days=1)
        
        print(f"dukascopy load {symbol} {start_date} {end_date}")

def main():
    parser = argparse.ArgumentParser(description="Check for gaps in tick data")
    
    parser.add_argument("symbol", help="Symbol to check (e.g., EURUSD)")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)", default=None)
    parser.add_argument("--end", help="End date (YYYY-MM-DD)", default=None)
    parser.add_argument("--interval", choices=["1d", "1w", "1M"], default="1d",
                        help="Analysis interval (1d=daily, 1w=weekly, 1M=monthly)")
    parser.add_argument("--threshold", type=int, default=500,
                        help="Minimum ticks per interval to consider complete (default: 500)")
    parser.add_argument("--visualize", action="store_true", 
                        help="Generate visualization of data coverage")
    parser.add_argument("--last", type=int, help="Check the last N days", default=None)
    
    args = parser.parse_args()
    
    # Calculate start and end dates if --last is used
    today = datetime.date.today()
    if args.last:
        end_date = today
        start_date = today - datetime.timedelta(days=args.last)
    else:
        # Use provided dates or defaults
        end_date = args.end if args.end else today
        
        # Default start date is 30 days before end date
        if args.start:
            start_date = args.start
        else:
            if isinstance(end_date, str):
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            start_date = end_date - datetime.timedelta(days=30)
    
    # Connect to database
    conn = connect_to_db()
    
    # Get data coverage
    coverage_data = get_data_coverage(conn, args.symbol, start_date, end_date, args.interval)
    
    # Identify gaps
    gaps = identify_data_gaps(coverage_data, args.threshold)
    
    # Print summary
    print(f"\n{'=' * 50}")
    print(f"Data Coverage Analysis for {args.symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'=' * 50}")
    
    # Print coverage data
    coverage_table_data = [(date.strftime('%Y-%m-%d'), count) for date, count in coverage_data]
    print_table(coverage_table_data, ["Date", "Tick Count"], "Full Coverage Data")
    
    # Print gaps
    if gaps:
        gaps_table_data = [(date.strftime('%Y-%m-%d'), count) for date, count in gaps]
        print_table(gaps_table_data, ["Date", "Tick Count"], f"Data Gaps (Threshold: {args.threshold} ticks)")
        
        # Suggest loading commands
        suggest_loading_command(args.symbol, gaps)
    else:
        print("\nNo data gaps found! All periods have sufficient tick data.")
    
    # Visualize if requested
    if args.visualize:
        visualize_coverage(coverage_data, args.symbol, args.interval)
    
    conn.close()

if __name__ == "__main__":
    main()