# QuestDB Limitations and Workarounds

## Data Modification Limitations

### No DELETE Support
QuestDB does not support `DELETE` operations for individual rows. The database follows an append-only model.

**Workaround:**
```sql
-- Create a new table without the unwanted data
CREATE TABLE market_data_clean AS (
    SELECT * FROM market_data
    WHERE condition_to_keep_data
);

-- Replace the original table
DROP TABLE market_data;
RENAME TABLE market_data_clean TO market_data;
```

### No UPDATE Support
Similar to DELETE, there is no support for updating individual records.

**Workaround:**
```sql
-- Create a table with updated values
CREATE TABLE market_data_updated AS (
    SELECT
        timestamp,
        symbol,
        -- Replace values conditionally
        CASE 
            WHEN condition THEN new_value 
            ELSE original_value 
        END AS value
    FROM market_data
);

-- Replace the original table
DROP TABLE market_data;
RENAME TABLE market_data_updated TO market_data;
```

## Query Limitations

### No HAVING Clause
QuestDB does not support the `HAVING` clause for filtering aggregated results.

**Workaround:**
```sql
-- Use a subquery instead
SELECT * FROM (
    SELECT symbol, avg(price) AS avg_price
    FROM market_data
    SAMPLE BY 1d
) WHERE avg_price > 100;
```

### Limited Subquery Support
Subqueries in the FROM clause are not supported.

**Workaround:**
```sql
-- Create a temporary table first
CREATE TABLE temp_result AS (
    SELECT symbol, avg(price) AS avg_price
    FROM market_data
    SAMPLE BY 1d
);

-- Then query it
SELECT * FROM temp_result
WHERE avg_price > 100;

-- Clean up when done
DROP TABLE temp_result;
```

### No WITH Clause
The WITH clause (Common Table Expressions) is not supported.

**Workaround:** Use temporary tables as shown above.

## SAMPLE BY Limitations

### Cannot Chain SAMPLE BY Operations
You cannot apply SAMPLE BY to already sampled data.

**Workaround:**
```sql
-- WRONG: This will fail
SELECT * FROM (
    SELECT * FROM market_data SAMPLE BY 1m
) SAMPLE BY 1h;

-- CORRECT: Always sample from original data
SELECT * FROM market_data SAMPLE BY 1h;
```

### Cannot Mix SAMPLE BY with Certain Operations
SAMPLE BY cannot be used with LATEST BY or certain other operations.

**Workaround:**
```sql
-- Create intermediate tables for each operation
CREATE TABLE hourly_data AS (
    SELECT * FROM market_data SAMPLE BY 1h
);

-- Then apply other operations
SELECT * FROM hourly_data LATEST BY symbol;
```

## Join Limitations

### Limited Join Types
QuestDB primarily supports equi-joins. Complex join conditions may not work.

**Workaround:**
```sql
-- Create a table with the needed keys for joining
CREATE TABLE prepared_data AS (
    SELECT *, 
           cast(timestamp as date) AS date_key
    FROM market_data
);

-- Then join on simple equality
SELECT a.*, b.*
FROM prepared_data a
JOIN reference_data b ON a.date_key = b.date;
```

### Performance with Large Joins
Joins on large tables can be slow.

**Workaround:**
- Filter data before joining
- Use designated timestamp columns
- Partition tables appropriately
- Create smaller, focused tables for joining