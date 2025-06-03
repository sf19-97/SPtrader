# QuestDB SQL Syntax Guide

## Core SQL Features and Limitations

### ✅ Supported Features
- `SAMPLE BY` for time-based aggregation
- `LATEST BY` for retrieving the most recent records
- `PARTITION BY` for time-based partitioning
- Symbol type for efficient string storage
- Native timestamp functions
- Time-series indexing

### ❌ Unsupported Features
- `DELETE FROM table WHERE condition` (use table recreation instead)
- `WITH` clauses (use temporary tables)
- `HAVING` clause (filter in subquery)
- Subqueries in FROM clause (use table creation)
- `UPDATE` statements (append-only model)
- Complex joins (only equi-joins supported)

## Time Series Operations

### SAMPLE BY (Time Aggregation)
```sql
-- CORRECT: Sample from raw data
SELECT timestamp, symbol,
       first(bid) as open,
       max(bid) as high,
       min(bid) as low,
       last(bid) as close
FROM market_data
SAMPLE BY 5m ALIGN TO CALENDAR;

-- WRONG: Cannot sample from sampled data
SELECT * FROM ohlc_1m SAMPLE BY 5m; -- FAILS!
```

### LATEST BY (Most Recent Records)
```sql
-- Get the latest price for each symbol
SELECT * FROM market_data
LATEST BY symbol;

-- With WHERE clause
SELECT * FROM market_data
WHERE symbol IN ('EURUSD', 'GBPUSD')
LATEST BY symbol;
```

### Timestamp Operations
```sql
-- Cast to timestamp
SELECT cast('2022-01-01T00:00:00.000Z' as timestamp) as ts;

-- Timestamp arithmetic (add 1 day)
SELECT dateadd('d', 1, timestamp) FROM market_data;

-- Extract parts
SELECT timestamp, 
       extract(year from timestamp) as year,
       extract(month from timestamp) as month
FROM market_data;
```

## Table Operations

### Creating Tables
```sql
-- Create table with designated timestamp
CREATE TABLE market_data (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    bid DOUBLE,
    ask DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

### Handling Deletes (Workaround)
```sql
-- Create new table without unwanted records
CREATE TABLE market_data_new AS (
    SELECT * FROM market_data
    WHERE timestamp > '2022-01-01'
);

-- Drop old table and rename new one
DROP TABLE market_data;
RENAME TABLE market_data_new TO market_data;
```

## Common Aggregation Patterns

### OHLC Calculation
```sql
-- Generate OHLC candles
SELECT 
    timestamp,
    symbol,
    first(price) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price) AS close,
    sum(volume) AS volume
FROM trades
SAMPLE BY 1h ALIGN TO CALENDAR;
```

### Downsampling
```sql
-- Downsample time series data
SELECT 
    timestamp,
    avg(value) AS avg_value,
    min(value) AS min_value,
    max(value) AS max_value,
    count(*) AS sample_count
FROM sensor_data
SAMPLE BY 5m ALIGN TO CALENDAR;
```