# Root Cause Analysis: Inconsistent Data Loading

## The Problem
1. **Incomplete Data**: March 2024 only has 5 days of data
2. **Poor Quality Days**: Many days have <2k ticks (holidays, data issues)
3. **Simple Date Math**: Frontend just subtracts days without checking data availability
4. **Different Views**: Each timeframe shows different data because they calculate ranges differently

## Why It Happens
```
Database end: 2024-03-05 00:59:50 (only 654 ticks that day!)

For 5m chart:
- end = March 5
- start = March 5 - 1 day = March 4
- Result: Only shows March 4!

For 1h chart:
- end = March 5  
- start = March 5 - 1 month = Feb 5
- Result: Shows Feb 5 - March 5 (includes many bad days)
```

## The Solution

### Option 1: Fix the Data (Recommended)
1. **Delete bad days** from the database
2. **Re-download missing data** to fill gaps
3. **Ensure March 2024 is complete**

### Option 2: Work Around Bad Data
1. **Create a data quality table** that tracks good/bad days
2. **Update frontend** to skip bad days
3. **Use intelligent date selection**

### Option 3: Quick Fix (Current Attempt)
1. **Hardcode to use Feb 27** as the end date (last known good day)
2. **Problem**: This is a band-aid, not a solution

## Recommended Action

```bash
# 1. Check which days need fixing
curl -G 'http://localhost:9000/exec' --data-urlencode "query=
SELECT DATE_TRUNC('day', timestamp) as day, COUNT(*) as ticks
FROM market_data_v2
WHERE symbol='EURUSD' AND COUNT(*) < 10000
GROUP BY day ORDER BY day DESC"

# 2. Delete bad days
curl -G 'http://localhost:9000/exec' --data-urlencode "query=
DELETE FROM market_data_v2 
WHERE symbol='EURUSD' 
  AND DATE_TRUNC('day', timestamp) IN (
    '2024-03-05', '2024-02-29', '2024-02-28'
  )"

# 3. Re-download the data properly
python3 data_feeds/dukascopy_to_ilp_batched.py EURUSD 2024-02-28 2024-03-31
```

This will give you consistent, high-quality data across all timeframes.