-- Time Filtering Examples for QuestDB
-- These examples show efficient ways to filter time series data

-- Basic time range filtering
SELECT *
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02';

-- Time range with symbol filter (timestamp filter first for better performance)
SELECT *
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02'
  AND symbol = 'EURUSD';

-- Filter by specific days
SELECT *
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-31'
  AND extract(dow from timestamp) IN (1, 2, 3, 4, 5);  -- Monday to Friday

-- Filter by time of day (trading hours: 9:30 AM to 4:00 PM)
SELECT *
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-31'
  AND extract(hour from timestamp) * 100 + extract(minute from timestamp) BETWEEN 930 AND 1600;

-- Filter for specific hour ranges
SELECT *
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-31'
  AND extract(hour from timestamp) BETWEEN 9 AND 16;

-- Relative time filtering (last 24 hours)
SELECT *
FROM market_data
WHERE timestamp > dateadd('d', -1, now());

-- Relative time filtering (last 7 days)
SELECT *
FROM market_data
WHERE timestamp > dateadd('d', -7, now());

-- Relative time filtering (last month)
SELECT *
FROM market_data
WHERE timestamp > dateadd('m', -1, now());

-- Filter by month
SELECT *
FROM market_data
WHERE extract(year from timestamp) = 2023
  AND extract(month from timestamp) = 1;  -- January

-- Time-based partitioning example (assuming PARTITION BY DAY)
-- This is very efficient as it uses the partition pruning feature
SELECT *
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07';

-- Combining multiple time conditions
SELECT *
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-31'
  AND extract(dow from timestamp) IN (1, 2, 3, 4, 5)  -- Weekdays only
  AND extract(hour from timestamp) BETWEEN 9 AND 16;  -- Trading hours

-- Working with different timezones
-- Convert UTC to EST (UTC-5)
SELECT 
    timestamp AS utc_time,
    dateadd('h', -5, timestamp) AS est_time,
    price
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02';

-- Filter by EST trading hours (9:30 AM to 4:00 PM EST)
SELECT *
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-31'
  AND extract(hour from dateadd('h', -5, timestamp)) * 100 + 
      extract(minute from dateadd('h', -5, timestamp)) BETWEEN 930 AND 1600;