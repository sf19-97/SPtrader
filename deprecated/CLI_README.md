# SPtrader CLI

A unified command-line interface for managing all SPtrader services.

## Installation

```bash
./install_cli.sh
```

This will:
- Create a symlink to the `sptrader` command
- Add `~/.local/bin` to your PATH if needed
- Allow you to run `sptrader` from anywhere

## Usage

```bash
sptrader <command> [options]
```

## Commands

### Service Management
- `sptrader start` - Start all services
- `sptrader stop` - Stop all services  
- `sptrader restart` - Restart all services
- `sptrader status` - Check service status
- `sptrader monitor` - Real-time monitoring dashboard

### Logs
- `sptrader logs` - View recent logs from all services
- `sptrader logs -f` - Follow logs in real-time

### API Management
- `sptrader api health` - Check API health
- `sptrader api stats` - View API statistics
- `sptrader api docs` - Open API documentation
- `sptrader api test` - Run API tests

### Database Management
- `sptrader db console` - Open QuestDB web console
- `sptrader db query '<SQL>'` - Execute a SQL query
- `sptrader db stats` - View database statistics

### Optimization & Testing
- `sptrader optimize` - Run QuestDB viewport optimizations
- `sptrader test` - Run all tests

## Examples

```bash
# Start all services
sptrader start

# Check what's running
sptrader status

# Monitor in real-time
sptrader monitor

# Follow logs
sptrader logs -f

# Check API health
sptrader api health

# Query database
sptrader db query 'SELECT count(*) FROM ohlc_5m_v2'

# Run optimizations
sptrader optimize
```

## Quick Actions in Monitor

When running `sptrader monitor`, you can press:
- `L` - View logs
- `S` - Stop all services
- `R` - Restart services
- `Q` - Quit monitor

## Service URLs

After starting services:
- QuestDB Console: http://localhost:9000
- FastAPI Backend: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- React Frontend: http://localhost:5173 (if configured)