#!/usr/bin/env python3
"""
Populate the data_quality table with daily statistics
This allows the system to make intelligent decisions about data ranges
"""

import requests
import json
from datetime import datetime, timedelta

QUESTDB_URL = "http://localhost:9000/exec"

def calculate_quality_score(tick_count, hours_coverage):
    """Calculate a quality score from 0-100"""
    # Base score from tick count (max 80 points)
    if tick_count >= 100000:
        tick_score = 80
    elif tick_count >= 50000:
        tick_score = 70
    elif tick_count >= 20000:
        tick_score = 50
    elif tick_count >= 10000:
        tick_score = 30
    elif tick_count >= 5000:
        tick_score = 20
    else:
        tick_score = tick_count / 5000 * 20
    
    # Hours coverage score (max 20 points)
    hour_score = (hours_coverage / 24) * 20
    
    return tick_score + hour_score

def get_quality_rating(score):
    """Convert score to rating"""
    if score >= 90:
        return "EXCELLENT"
    elif score >= 70:
        return "GOOD"
    elif score >= 50:
        return "FAIR"
    elif score >= 30:
        return "POOR"
    else:
        return "BAD"

def populate_data_quality():
    print("📊 Populating data quality table...")
    
    # First, clear existing data
    clear_query = "TRUNCATE TABLE data_quality"
    requests.get(QUESTDB_URL, params={"query": clear_query})
    
    # Get daily statistics
    stats_query = """
    SELECT 
        'EURUSD' as symbol,
        DATE_TRUNC('day', timestamp) as trading_date,
        COUNT(*) as tick_count,
        MIN(timestamp) as first_tick,
        MAX(timestamp) as last_tick,
        COUNT(DISTINCT EXTRACT(hour FROM timestamp)) as hours_coverage
    FROM market_data_v2
    WHERE symbol = 'EURUSD'
    GROUP BY trading_date
    ORDER BY trading_date
    """
    
    response = requests.get(QUESTDB_URL, params={"query": stats_query})
    if not response.ok:
        print(f"❌ Failed to get statistics: {response.text}")
        return
    
    data = response.json()
    
    print(f"Processing {len(data['dataset'])} days...")
    
    # Process each day
    insert_count = 0
    for row in data['dataset']:
        symbol = row[0]
        trading_date = row[1]
        tick_count = row[2]
        first_tick = row[3]
        last_tick = row[4]
        hours_coverage = row[5]
        
        # Calculate quality metrics
        quality_score = calculate_quality_score(tick_count, hours_coverage)
        quality_rating = get_quality_rating(quality_score)
        is_complete = tick_count >= 10000 and hours_coverage >= 20
        
        # Insert into data_quality table
        insert_query = f"""
        INSERT INTO data_quality VALUES(
            '{symbol}',
            '{trading_date}',
            {tick_count},
            '{first_tick}',
            '{last_tick}',
            {hours_coverage},
            {quality_score},
            '{quality_rating}',
            {str(is_complete).lower()},
            NOW()
        )
        """
        
        response = requests.get(QUESTDB_URL, params={"query": insert_query})
        if response.ok:
            insert_count += 1
            if insert_count % 50 == 0:
                print(f"  Processed {insert_count} days...")
    
    print(f"✅ Populated {insert_count} days of quality data")
    
    # Show summary
    summary_query = """
    SELECT 
        quality_rating,
        COUNT(*) as days,
        AVG(tick_count) as avg_ticks,
        AVG(quality_score) as avg_score
    FROM data_quality
    WHERE symbol = 'EURUSD'
    GROUP BY quality_rating
    ORDER BY avg_score DESC
    """
    
    response = requests.get(QUESTDB_URL, params={"query": summary_query})
    if response.ok:
        data = response.json()
        print("\n📈 Quality Summary:")
        print(f"{'Rating':<12} {'Days':<8} {'Avg Ticks':<12} {'Avg Score':<10}")
        print("-" * 45)
        for row in data['dataset']:
            print(f"{row[0]:<12} {row[1]:<8} {row[2]:<12,.0f} {row[3]:<10.1f}")

if __name__ == "__main__":
    populate_data_quality()