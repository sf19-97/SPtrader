#!/usr/bin/env python3
"""
Test ILP connection using the Go ingestion service
"""

import json
import subprocess
import sys
import os
import datetime
import time

# Test data
now = datetime.datetime.now(datetime.timezone.utc)
test_tick = {
    "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "symbol": "EURUSD",
    "bid": 1.0883,
    "ask": 1.0884,
    "price": 1.08835,
    "spread": 0.0001,
    "volume": 5.0,
    "bid_volume": 3.0,
    "ask_volume": 2.0,
    "hour_of_day": now.hour,
    "day_of_week": now.weekday() + 1,
    "trading_session": "TEST",
    "market_open": True
}

# Create test data with 10 ticks
test_data = []
for i in range(10):
    tick = test_tick.copy()
    timestamp = (now + datetime.timedelta(seconds=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
    tick["timestamp"] = timestamp
    test_data.append(tick)

# Path to Go ingestion binary
ingestion_binary = "/tmp/test_ilp"

print(f"Sending {len(test_data)} test ticks to Go ILP service...")

try:
    # Launch Go ingestion service with Python mode
    process = subprocess.Popen(
        [ingestion_binary, "-python"],
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Send JSON data to the process
    json_data = json.dumps(test_data).encode('utf-8')
    stdout, stderr = process.communicate(input=json_data, timeout=10)
    
    # Print results
    print("STDOUT:", stdout.decode())
    print("STDERR:", stderr.decode())
    
    if process.returncode == 0:
        print("✅ Successfully sent test data via Go ILP client")
    else:
        print(f"❌ Error: Go ILP client exited with code {process.returncode}")
        
except Exception as e:
    print(f"❌ Error: {e}")