# QuestDB Best Practices

## Table Design

### Use Designated Timestamp
Always specify a designated timestamp column for time-series data:

```sql
CREATE TABLE market_data (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

Benefits:
- Improved query performance
- Efficient time range filtering
- Better partitioning

### Choose Appropriate Partitioning
Select partitioning based on:
- Data volume
- Query patterns
- Retention policies

```sql
-- For high-frequency data
PARTITION BY DAY

-- For daily summary data
PARTITION BY MONTH

-- For sparse data
PARTITION BY YEAR
```

### Use Symbol Type for Strings
Use the SYMBOL type for repeated string values:

```sql
CREATE TABLE trades (
    timestamp TIMESTAMP,
    symbol SYMBOL,     -- Better than VARCHAR for repeated values
    trader VARCHAR,    -- Better than SYMBOL for unique values
    price DOUBLE
);
```

Symbol type offers:
- Memory efficiency
- Faster comparisons
- Better indexing

## Query Optimization

### Filter on Timestamp First
Always filter on the designated timestamp first:

```sql
-- GOOD: Timestamp filter first
SELECT * FROM market_data 
WHERE timestamp > '2022-01-01' 
  AND symbol = 'EURUSD';

-- LESS EFFICIENT: Non-timestamp filter first
SELECT * FROM market_data 
WHERE symbol = 'EURUSD' 
  AND timestamp > '2022-01-01';
```

### Use Appropriate Time Ranges
Avoid querying very large time ranges when possible:

```sql
-- Better to do multiple targeted queries than one large one
SELECT * FROM high_frequency_data 
WHERE timestamp BETWEEN '2022-01-01' AND '2022-01-07';
```

### Optimize SAMPLE BY Queries
For SAMPLE BY operations:

```sql
-- Include ALIGN TO CALENDAR for consistent boundaries
SELECT timestamp, avg(value)
FROM sensor_data
SAMPLE BY 1h ALIGN TO CALENDAR;

-- Specify fill behavior for gaps
SELECT timestamp, avg(value)
FROM sensor_data
SAMPLE BY 1h FILL(NULL);
```

## Data Import and Management

### Bulk Data Loading
Prefer bulk imports over individual inserts:

```sql
-- Better than many small inserts
INSERT INTO market_data
SELECT * FROM COPY('data.csv');
```

### Table Lifecycle Management
Implement regular cleanup policies:

```sql
-- Create a retention policy script
CREATE TABLE market_data_retained AS (
    SELECT * FROM market_data
    WHERE timestamp > dateadd('d', -90, now())
);

DROP TABLE market_data;
RENAME TABLE market_data_retained TO market_data;
```

### Pre-aggregate Common Views
Pre-compute common aggregations:

```sql
-- Create hourly aggregation table
CREATE TABLE market_data_hourly AS (
    SELECT 
        timestamp,
        symbol,
        first(price) AS open,
        max(price) AS high,
        min(price) AS low,
        last(price) AS close
    FROM market_data
    SAMPLE BY 1h ALIGN TO CALENDAR
);
```

## Performance Tuning

### Memory Management
Adjust memory settings in questdb.conf:

```properties
# Increase Cairo page pool size for better performance
cairo.sql.sort.page.size=16777216
cairo.sql.sort.key.page.size=16777216
```

### Optimize Timestamp Usage
Use microsecond precision only when needed:

```sql
-- For most financial data, millisecond precision is sufficient
timestamp TIMESTAMP(3)  -- Millisecond precision
```

### Monitor Query Performance
Use built-in tools to identify slow queries:

```sql
-- Check table sizes
SELECT name, partitionCount, designatedTimestamp, walEnabled
FROM tables();

-- Check table sizes
SELECT name, size()
FROM tables();
```