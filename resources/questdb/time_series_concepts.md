# QuestDB Time Series Concepts

## Overview

QuestDB is designed specifically for time-series data, with optimizations that make it significantly faster than general-purpose databases for time-based operations. Understanding these core concepts is essential for effective use of QuestDB.

## Designated Timestamp

The designated timestamp is a special timestamp column that receives preferential treatment in QuestDB.

### Definition and Benefits

```sql
-- Creating a table with a designated timestamp
CREATE TABLE sensor_data (
    timestamp TIMESTAMP,  -- This will be the designated timestamp
    sensor_id SYMBOL,
    value DOUBLE
) TIMESTAMP(timestamp);  -- This designates the timestamp column
```

Key benefits:
- Efficient time-based filtering
- Optimized time-based partitioning
- Improved performance for time range queries
- Enhanced SAMPLE BY operations

### Timestamp Precision

QuestDB supports microsecond precision, but you can optimize storage by specifying precision:

```sql
-- Microsecond precision (default)
timestamp TIMESTAMP  

-- Millisecond precision (reduces storage requirements)
timestamp TIMESTAMP(3)
```

### Rules and Constraints

1. Only one designated timestamp per table
2. Cannot contain NULL values
3. Must be strictly ascending when appending data within a single transaction
4. Cannot be modified after table creation

## Partitioning

Partitioning divides data into smaller chunks based on time, improving query performance and data management.

### Partition Types

```sql
-- Daily partitioning (best for high-frequency data)
CREATE TABLE market_data_daily (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- Monthly partitioning (for less frequent data)
CREATE TABLE market_data_monthly (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE
) TIMESTAMP(timestamp) PARTITION BY MONTH;

-- Yearly partitioning (for sparse data)
CREATE TABLE market_data_yearly (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE
) TIMESTAMP(timestamp) PARTITION BY YEAR;
```

### Partition Benefits

1. **Query Optimization**: QuestDB only scans relevant partitions based on timestamp filters
2. **Storage Efficiency**: Similar data stored together improves compression
3. **Data Lifecycle Management**: Easier to drop older partitions
4. **Concurrent Processing**: Partitions can be processed in parallel

### Partition Selection

Choose based on:
1. Data volume
2. Query patterns
3. Retention needs

## SAMPLE BY

SAMPLE BY is QuestDB's time-based aggregation mechanism, similar to GROUP BY but specifically for time intervals.

### Basic Usage

```sql
-- Basic SAMPLE BY with 1-hour intervals
SELECT timestamp, avg(value)
FROM sensor_data
SAMPLE BY 1h;

-- With calendar alignment (recommended)
SELECT timestamp, avg(value)
FROM sensor_data
SAMPLE BY 1h ALIGN TO CALENDAR;

-- With fill behavior for gaps
SELECT timestamp, avg(value)
FROM sensor_data
SAMPLE BY 1h FILL(NULL);
```

### Time Units

- `s`: seconds
- `m`: minutes
- `h`: hours
- `d`: days
- `M`: months
- `y`: years

### Alignment Options

```sql
-- Default in newer versions (time buckets align to calendar)
SAMPLE BY 1d ALIGN TO CALENDAR

-- Align to first observation
SAMPLE BY 1d ALIGN TO FIRST OBSERVATION
```

### Fill Behavior

```sql
-- No filling (gaps in data = gaps in results)
SAMPLE BY 1h

-- Fill with NULL
SAMPLE BY 1h FILL(NULL)

-- Fill with a constant value
SAMPLE BY 1h FILL(0)

-- Fill with the previous value
SAMPLE BY 1h FILL(PREV)

-- Fill with linear interpolation
SAMPLE BY 1h FILL(LINEAR)

-- Mixed fill strategies (by column position)
SAMPLE BY 1h FILL(NULL, PREV, LINEAR)
```

### Limitations

1. Cannot chain SAMPLE BY operations
2. Cannot use SAMPLE BY with LATEST BY
3. Always requires a designated timestamp

## LATEST BY

LATEST BY retrieves the most recent record based on the designated timestamp for each unique value of a column.

### Basic Usage

```sql
-- Get latest value for each sensor
SELECT * FROM sensor_data
LATEST BY sensor_id;

-- With filtering
SELECT * FROM sensor_data
WHERE location = 'warehouse'
LATEST BY sensor_id;

-- Latest values for multiple fields
SELECT * FROM sensor_data
LATEST BY sensor_id, location;
```

### Combined with Time Filtering

```sql
-- Latest value for each sensor within the last 24 hours
SELECT * FROM sensor_data
WHERE timestamp > dateadd('d', -1, now())
LATEST BY sensor_id;
```

## Symbol Type

The SYMBOL data type is optimized for repeated string values, making it ideal for categories, IDs, and codes.

### Usage

```sql
CREATE TABLE trades (
    timestamp TIMESTAMP,
    symbol SYMBOL,       -- Use for ticker symbols, limited set
    trader_id SYMBOL,    -- Use for trader IDs, repeated values
    notes VARCHAR        -- Use VARCHAR for unique text
) TIMESTAMP(timestamp);
```

### Benefits

1. **Storage Efficiency**: Symbol values are stored once and referenced
2. **Query Performance**: Faster comparisons and joins
3. **Automatic Indexing**: SYMBOL columns are automatically indexed
4. **Memory Efficiency**: String pool architecture saves RAM

### Best Practices

- Use SYMBOL for values from a limited set that repeat frequently
- Use VARCHAR for unique or rarely repeated strings
- Monitor string pool size with `SELECT symbolPoolCapacity()`

## Write-Ahead Log (WAL)

WAL improves write performance by storing changes in a log before applying them to tables.

### Enabling WAL

```sql
-- Enable WAL for a table
CREATE TABLE realtime_data (
    timestamp TIMESTAMP,
    sensor_id SYMBOL,
    value DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Check WAL status
SELECT name, walEnabled
FROM tables();
```

### Benefits

1. **Write Performance**: Better throughput for high-frequency inserts
2. **Durability**: Protection against data loss on crashes
3. **Concurrent Operations**: Allows reads while writing

### Considerations

- Slightly increased disk usage
- Best for real-time data ingestion scenarios
- May require tuning of commit lag and max uncommitted rows

## Commit Settings

Control when data is committed to disk for performance optimization.

### Configuration

```sql
CREATE TABLE market_data (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY
WITH maxUncommittedRows=10000, commitLag=120000000;
```

Parameters:
- `maxUncommittedRows`: Maximum rows before committing (default: 10,000)
- `commitLag`: Maximum microseconds data can remain uncommitted (default: 30,000,000 = 30 seconds)

### Usage Scenarios

- **Batch Loading**: Increase `maxUncommittedRows` for faster bulk loading
- **Real-time Data**: Lower `commitLag` for more frequent persistence
- **Memory-constrained Systems**: Lower `maxUncommittedRows` to reduce memory pressure

## Best Practices Summary

1. **Always use a designated timestamp** for time series data
2. **Choose appropriate partitioning** based on data volume and query patterns
3. **Use SYMBOL type** for repeated string values
4. **Apply SAMPLE BY with ALIGN TO CALENDAR** for consistent time buckets
5. **Filter on timestamp first** in queries to leverage partition pruning
6. **Enable WAL** for write-heavy workloads
7. **Tune commit settings** based on your ingestion patterns
8. **Use appropriate timestamp precision** to balance accuracy and storage