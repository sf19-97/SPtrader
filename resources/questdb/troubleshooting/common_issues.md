# Common QuestDB Issues and Solutions

## Query Errors

### "Cannot SAMPLE BY on a query that already has SAMPLE BY"

**Problem:** Attempting to apply SAMPLE BY to already sampled data.

```sql
-- This will fail
SELECT * FROM (
    SELECT * FROM market_data SAMPLE BY 1m
) SAMPLE BY 1h;
```

**Solution:** Always sample directly from the source data:

```sql
-- Correct approach
SELECT * FROM market_data SAMPLE BY 1h;
```

### "LATEST BY and SAMPLE BY cannot be used together"

**Problem:** Mixing incompatible operations.

```sql
-- This will fail
SELECT * FROM market_data 
LATEST BY symbol 
SAMPLE BY 1h;
```

**Solution:** Use separate queries or temporary tables:

```sql
-- First get latest data
CREATE TABLE latest_data AS (
    SELECT * FROM market_data LATEST BY symbol
);

-- Then sample if needed
SELECT * FROM latest_data SAMPLE BY 1h;
```

### "Column X designated as timestamp but has nulls"

**Problem:** Designated timestamp column contains NULL values.

**Solution:** Filter out NULL timestamps before inserting or creating tables:

```sql
CREATE TABLE clean_data AS (
    SELECT * FROM raw_data
    WHERE timestamp IS NOT NULL
);
```

## Performance Issues

### Slow Queries on Large Time Ranges

**Problem:** Queries covering large time ranges are slow.

**Solution:**
1. Ensure proper partitioning (by DAY for high-frequency data)
2. Put timestamp filter first in WHERE clause
3. Break into smaller time chunks

```sql
-- Better than one large query
SELECT * FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07'
  AND symbol = 'EURUSD';
```

### High Memory Usage

**Problem:** QuestDB using too much memory during queries.

**Solution:**
1. Limit result sets with WHERE clauses
2. Use LIMIT for testing queries
3. Adjust memory settings in questdb.conf:

```properties
cairo.max.map.ram.percent=30
```

### Slow Joins

**Problem:** Joins between large tables are very slow.

**Solution:**
1. Filter tables before joining
2. Create smaller, focused tables for joining
3. Use designated timestamp columns

```sql
-- Filter before joining
SELECT a.*, b.*
FROM (SELECT * FROM large_table_a WHERE timestamp > dateadd('d', -7, now())) a
JOIN (SELECT * FROM large_table_b WHERE timestamp > dateadd('d', -7, now())) b
ON a.symbol = b.symbol;
```

## Data Import Issues

### Data Import Fails or Is Very Slow

**Problem:** CSV or other data imports fail or take too long.

**Solution:**
1. Split large files into smaller chunks
2. Check for data format issues
3. Increase import thread count

```bash
# From the command line
java -Dcairo.max.file.import.threads=4 -jar questdb.jar
```

### Timestamp Parse Errors

**Problem:** Timestamp formats not recognized during import.

**Solution:** Ensure timestamp format matches expected format:

```sql
-- For CSV imports, specify format
CREATE TABLE market_data AS (
    SELECT * FROM COPY('/path/to/data.csv') (
        timestamp DATE FORMAT 'yyyy-MM-dd''T''HH:mm:ss.SSSUUU'
    )
);
```

## System Issues

### QuestDB Won't Start

**Problem:** Server fails to start.

**Solution:**
1. Check logs in `log/questdb.log`
2. Ensure correct permissions on data directory
3. Verify ports are not in use:

```bash
# Check if port 9000 is in use
netstat -tuln | grep 9000
```

### Out of Disk Space

**Problem:** QuestDB stops working due to disk space issues.

**Solution:**
1. Implement data retention policies
2. Check for large WAL files
3. Remove unused tables

```sql
-- List all tables and their sizes
SELECT name, size() FROM tables();

-- Implement retention policy
CREATE TABLE market_data_retained AS (
    SELECT * FROM market_data
    WHERE timestamp > dateadd('d', -90, now())
);
DROP TABLE market_data;
RENAME TABLE market_data_retained TO market_data;
```

## Application Integration Issues

### Connection Refused

**Problem:** Applications can't connect to QuestDB.

**Solution:**
1. Check if QuestDB is running
2. Verify correct host/port configuration
3. Check firewall settings
4. Ensure correct API being used (REST, PostgreSQL, InfluxDB)

### Timezone Issues

**Problem:** Timestamps appear in wrong timezone.

**Solution:** QuestDB works in UTC. Adjust timestamps in application or queries:

```sql
-- Convert UTC to local time in queries
SELECT 
    timestamp AS utc_time,
    dateadd('h', -5, timestamp) AS local_time,
    value
FROM sensor_data;
```