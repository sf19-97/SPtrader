# QuestDB CLI

*Created: May 31, 2025*

A command-line interface for QuestDB database management in the SPtrader project. This tool provides easy access to database operations, schema management, data visualization, and performance monitoring - all from the command line.

## Overview

QuestDB CLI simplifies database interactions with an intuitive command-line interface. It helps you query data, generate OHLC candles, export results, inspect tables, and test API endpoints.

## Installation

The tool is pre-installed in the SPtrader repository. All dependencies are isolated within the `tools/questdb-cli` directory and do not affect other parts of the codebase.

### Quick Setup

Run the setup script to configure the CLI for your environment:

```bash
cd /home/millet_frazier/SPtrader/tools/questdb-cli
./setup.sh
```

Or run the configuration wizard directly:

```bash
cd /home/millet_frazier/SPtrader/tools/questdb-cli
./questdb-cli.sh config --setup
```

## Usage

```bash
./questdb-cli.sh <command> [options]
```

Or use the full path:

```bash
/home/millet_frazier/SPtrader/tools/questdb-cli/questdb-cli.sh <command> [options]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `query` | Execute SQL queries against QuestDB |
| `table-info` | Get information about database tables |
| `export` | Export query results to files |
| `generate-ohlc` | Generate OHLC candles from tick data |
| `test-endpoint` | Test API endpoints with database data |
| `config` | Manage CLI configuration |
| `help` | Show help information |

## Command Examples

### Execute a Query

```bash
# Run a simple query
./questdb-cli.sh query "SELECT * FROM ohlc_1m_v2 WHERE symbol = 'EURUSD' LIMIT 10"

# Export query results to JSON
./questdb-cli.sh query "SELECT * FROM ohlc_1h_v2 WHERE symbol = 'EURUSD'" --format json --output eurusd_hourly.json

# Use PostgreSQL wire protocol instead of HTTP
./questdb-cli.sh query "SELECT * FROM market_data_v2 LIMIT 10" --protocol pg
```

### View Table Information

```bash
# List all tables
./questdb-cli.sh table-info

# Get information about a specific table
./questdb-cli.sh table-info ohlc_1m_v2

# Show detailed information including columns
./questdb-cli.sh table-info market_data_v2 --all
```

### Export Data

```bash
# Export to CSV file
./questdb-cli.sh export "SELECT * FROM ohlc_1d_v2 WHERE symbol = 'EURUSD'" --format csv --output eurusd_daily.csv

# Export large dataset with batching
./questdb-cli.sh export "SELECT * FROM market_data_v2 WHERE symbol = 'EURUSD'" --format json --output eurusd_ticks.json --batch-size 50000
```

### Generate OHLC Candles

```bash
# Generate 1-minute candles
./questdb-cli.sh generate-ohlc EURUSD --timeframe 1m

# Generate 1-hour candles for a specific date range
./questdb-cli.sh generate-ohlc GBPUSD --timeframe 1h --start 2025-01-01 --end 2025-01-31

# Use a specific price field and overwrite existing data
./questdb-cli.sh generate-ohlc USDJPY --timeframe 4h --field price --overwrite
```

### Test API Endpoints

```bash
# Test candles endpoint
./questdb-cli.sh test-endpoint /candles --params "symbol=EURUSD&tf=1h&start=2025-01-01T00:00:00Z&end=2025-01-02T00:00:00Z"

# Compare API results with database query
./questdb-cli.sh test-endpoint /candles/lazy --params "symbol=EURUSD&tf=1h" --compare-query "SELECT * FROM ohlc_1h_v2 WHERE symbol = 'EURUSD' LIMIT 100" --verbose
```

### Configuration Management

```bash
# View current configuration
./questdb-cli.sh config --list

# Run interactive setup
./questdb-cli.sh config --setup

# Reset to default configuration
./questdb-cli.sh config --reset
```

## Configuration

QuestDB CLI uses a hierarchical configuration system:

1. **Default Configuration** (`config/default.json`): Base settings
2. **Environment Configuration** (`config/development.json`, `config/production.json`): Environment-specific overrides
3. **Local Configuration** (`config/local.json`): User-specific settings (gitignored)
4. **Environment Variables**: Highest precedence

### Configuration Files

The main configuration parameters:

```json
{
  "database": {
    "host": "localhost",
    "httpPort": 9000,
    "ilpPort": 9009,
    "pgPort": 8812,
    "username": "admin",
    "password": "quest",
    "timeout": 30000
  },
  "api": {
    "baseUrl": "http://localhost:8080/api/v1"
  },
  "defaults": {
    "format": "table",
    "limit": 100
  }
}
```

## Output Formats

The CLI supports multiple output formats:

- **Table**: Formatted ASCII tables (default for display)
- **JSON**: JSON objects (ideal for programmatic access and API integration)
- **CSV**: Comma-separated values (good for spreadsheets)

## Environment Variables

You can override configuration settings with environment variables:

```bash
# Set database connection
export QUESTDB_HOST=192.168.1.100
export QUESTDB_HTTP_PORT=9000

# Set output format
export QUESTDB_FORMAT=json

# Set environment
export NODE_ENV=production

# Run command
./questdb-cli.sh query "SELECT * FROM ohlc_1m_v2 LIMIT 10"
```

## Extending the CLI

### Adding a New Command

1. Create a new file in the `commands/` directory (e.g., `commands/my-command.js`)
2. Implement the command with the `registerCommand` function
3. Add documentation to this README

Example command structure:

```javascript
function registerCommand(program) {
  program
    .command('my-command')
    .description('Description of my command')
    .argument('<required-arg>', 'Description of argument')
    .option('-o, --option <value>', 'Description of option')
    .action(async (arg, options) => {
      // Command implementation
    });
}

module.exports = { registerCommand };
```

## Troubleshooting

### Connection Issues

- Verify QuestDB is running (`ps aux | grep questdb`)
- Check connection parameters in configuration
- Test direct access (`curl http://localhost:9000/exec?query=SELECT%201`)

### Execution Errors

- Check SQL syntax for queries
- Verify table and column names
- Look for timeout settings if queries are too complex

### Permission Problems

- Check file permissions for output directories
- Verify database user permissions

## License

Part of the SPtrader project.

---

*Documentation created by Claude, May 31, 2025*