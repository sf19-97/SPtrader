# SPtrader Interactive TUI Control Center - Complete Specification

## Project Overview
Create a Terminal User Interface (TUI) that serves as a complete control center for the SPtrader forex trading platform. This will replace/enhance the current monitor.sh with a full-featured, mouse-clickable interface that provides both real-time monitoring and complete system control, including CI/CD operations.

## Core Requirements

### 1. Display Layout
The interface should have these sections:

**Header Bar:**
- Title: "SPtrader Control Center"
- Current time (updates every second)
- System status indicator (All Systems Go / Issues Detected)
- Git branch indicator (if in git repo)

**Main Control Panel (Top Section):**
- Organized in 5 columns of clickable buttons:
  - Services
  - API
  - Database
  - Logs
  - DevOps (NEW)

**Live Monitoring Panel (Middle Section):**
- Real-time service status with memory usage
- Updates every 5 seconds
- Color coding: Green=running, Red=stopped, Yellow=warning

**Information Panel (Bottom Section):**
- Shows output from commands
- Scrollable text area
- Clear button to reset

**Status Bar (Footer):**
- Show last action performed
- Keyboard shortcuts reminder
- Connection status indicators

## 2. Required Functionality

### Service Management
- **Start All** - Execute: `/home/millet_frazier/SPtrader/start_background.sh`
- **Stop All** - Execute: `/home/millet_frazier/SPtrader/stop_all.sh`
- **Restart** - Stop all, wait 3 seconds, start all
- **Check Status** - Execute: `/home/millet_frazier/SPtrader/tools/check_services.sh`

### API Operations
- **Health Check** - GET http://localhost:8000/api/health
- **View Stats** - GET http://localhost:8000/api/stats and display formatted
- **Open Docs** - Launch browser to http://localhost:8000/docs
- **Run Tests** - Execute: `cd /home/millet_frazier/SPtrader/api && python test_api.py`

### Database Operations
- **Open Console** - Launch browser to http://localhost:9000
- **Quick Stats** - Query: `SELECT count(*) FROM ohlc_5m_v2`
- **Custom Query** - Pop up input dialog for SQL, execute via QuestDB API
- **Run Migrations** - Execute: `python /home/millet_frazier/SPtrader/migrations/migrate.py`

### Log Management
- **Follow Logs** - `tail -f /home/millet_frazier/SPtrader/logs/runtime/*.log`
- **Show Status** - Execute: `/home/millet_frazier/SPtrader/tools/manage_logs.sh show`
- **Clean Logs** - Execute: `/home/millet_frazier/SPtrader/tools/manage_logs.sh clean all`
- **Rotate Logs** - Execute: `/home/millet_frazier/SPtrader/tools/manage_logs.sh rotate`

### DevOps Operations (NEW - CI/CD Features)
- **Git Status** - Show current branch, uncommitted changes
- **Run Tests** - Execute full test suite with coverage report
- **Deploy** - Run deployment pipeline (with confirmation)
- **Rollback** - Revert to previous version
- **Build** - Create production build
- **Lint/Format** - Run code quality checks

## 3. CI/CD Integration Features

### Git Integration
```python
# Commands to implement
git_status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True)
current_branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True)
last_commit = subprocess.run(['git', 'log', '-1', '--oneline'], capture_output=True)
```

### Test Pipeline
Create test stages that show progress:
```
1. Pre-flight checks ✓
2. Unit tests       ✓
3. Integration tests ⟳ (running)
4. Performance tests
5. Security scan
```

### Deployment Pipeline
```
1. Build artifacts
2. Run migrations
3. Deploy services
4. Health checks
5. Smoke tests
```

### Quality Checks
- Python linting (flake8/pylint)
- Code formatting (black)
- Type checking (mypy)
- Security scanning (bandit)

## 4. Real-Time Monitoring Requirements

### Service Status Checks:
```bash
# QuestDB - Check process: pgrep -f "questdb.*ServerMain"
# FastAPI - Check process: pgrep -f "uvicorn.*main:app"  
# Oanda Feed - Check process: pgrep -f "oanda_feed.py"
# OHLC Manager - Check process: pgrep -f "ohlc_manager.py"
# React Frontend - Check process: pgrep -f "npm.*dev"
```

### CI/CD Status Indicators:
- Test coverage percentage
- Last deployment time
- Current version/tag
- Pipeline status (passed/failed)

## 5. Interactive Features

### Mouse Support:
- All buttons should be clickable
- Hover effects for better UX
- Scroll support in output panel

### Keyboard Shortcuts:
- F1-F5: Quick access to main sections
- Ctrl+T: Run tests
- Ctrl+D: Deploy
- Ctrl+G: Git status
- 'q' or ESC: Quit application

### Dialog Boxes:
- Deployment confirmation
- SQL query input
- Git commit message input
- Version tag input

## 6. DevOps Automation Scripts

Create these helper scripts in `/home/millet_frazier/SPtrader/devops/`:

**run_tests.sh:**
```bash
#!/bin/bash
echo "Running test suite..."
python -m pytest --cov=api --cov=scripts --cov-report=term-missing
```

**deploy.sh:**
```bash
#!/bin/bash
echo "Deployment pipeline starting..."
./run_tests.sh || exit 1
./migrations/migrate.py || exit 1
./stop_all.sh
./start_background.sh
./tools/test_connectivity.sh || exit 1
echo "Deployment complete!"
```

**quality_check.sh:**
```bash
#!/bin/bash
echo "Running quality checks..."
black --check .
flake8 .
mypy api/
```

## 7. Configuration File

Create `.sptrader_tui.yaml`:
```yaml
ci_cd:
  auto_test_on_save: true
  deployment_branch: main
  rollback_limit: 5
  test_timeout: 300

quality:
  black_line_length: 88
  flake8_max_complexity: 10
  mypy_strict: true

monitoring:
  refresh_interval: 5
  log_buffer_size: 1000
  alert_on_test_failure: true
```

## 8. Visual Design Requirements

### DevOps Section Colors:
- Git status: Yellow for uncommitted, Green for clean
- Tests: Green=passed, Red=failed, Yellow=running
- Deploy button: Blue, but Red if tests failing
- Quality indicators: Traffic light colors

### Unicode Characters to Use:
- ✅ for running services
- ❌ for stopped services
- ⚠️  for warnings
- 🔄 for refresh/restart
- 📊 for stats
- 🚀 for start
- 🛑 for stop

## 9. Implementation Architecture

```
/home/millet_frazier/SPtrader/tui/
├── sptrader_tui.py          # Main TUI application
├── modules/
│   ├── service_monitor.py   # Service monitoring
│   ├── api_client.py        # API interactions
│   ├── git_integration.py   # Git operations (NEW)
│   ├── ci_cd_pipeline.py    # CI/CD operations (NEW)
│   └── quality_checks.py    # Code quality (NEW)
└── config/
    └── tui_config.yaml      # Configuration
```

## 10. Example CI/CD Workflow in TUI

1. User makes code changes
2. TUI detects uncommitted changes (yellow indicator)
3. User clicks "Run Tests" button
4. TUI shows test progress in real-time
5. If tests pass, "Deploy" button becomes active
6. User clicks "Deploy" with confirmation
7. TUI runs deployment pipeline with progress
8. Success/failure notification
9. Option to rollback if needed

## Additional Specifications

### Script Execution Standards

**Output Handling:**
- All script outputs should be captured and displayed in the TUI's output panel
- Preserve ANSI color codes from bash scripts (your scripts use color)
- Show real-time output for long-running commands (don't wait for completion)
- Scripts that output JSON should be parsed and formatted nicely

**Error Handling:**
- Check exit codes from all script executions
- If a script fails (non-zero exit), show error in red
- Common errors to handle gracefully:
  - QuestDB not running when trying to query
  - API not responding on port 8000
  - Permission denied errors

### State Management

**Don't Cache Status:**
- Always call check scripts for current state
- Don't assume a service is still running from last check
- Refresh status before any action (e.g., check if services are running before "restart")

**Background Updates:**
- Status checks should run in background threads
- UI should never freeze during script execution
- Show spinner/loading indicator during operations

### Script Dependencies

**Required Shell Commands:**
The TUI should verify these are available on startup:
- `curl` - Used for API calls
- `pgrep` - Used for process checking
- `netstat` or `ss` - Used for port checking
- `python3` - Used for various scripts

**Environment Variables:**
- Respect `SPTRADER_HOME` if set, otherwise use `/home/millet_frazier/SPtrader`
- Pass through user's PATH for script execution

### Special Behaviors to Preserve

**Start Services Sequence:**
- `start_background.sh` has built-in delays and health checks
- Show its output in real-time so user sees the startup sequence
- Don't timeout too quickly - QuestDB can take 10+ seconds

**Log Following:**
- When showing logs, allow user to filter by service
- Highlight ERROR and WARNING lines
- Allow user to stop following with ESC or 'q'

**Database Queries:**
- Queries go to `http://localhost:9000/exec`
- Results come back as JSON with dataset array
- Empty results are not an error

### Configuration & Persistence

**Settings to Remember** (store in `~/.sptrader_tui.conf`):
- Last window size
- Preferred refresh interval (default 5 seconds)
- Whether to auto-start services on TUI launch
- Custom keybindings

**Don't Persist:**
- Service status
- API statistics  
- Log content

### Integration Points

**With SPtrader-login.py:**
- The TUI should accept a `--skip-start` flag
- If not provided, auto-run start_background.sh on launch
- This lets the auth wrapper control startup behavior

**With existing monitor.sh:**
- The TUI replaces monitor.sh functionality
- But monitor.sh should still work independently
- Consider adding "Launch Old Monitor" option in TUI

### Failure Modes

**If TUI Can't Start:**
- Fall back to launching regular `sptrader` CLI
- Show clear error message about what failed
- Don't leave user with nothing

**If All Services Down:**
- TUI should still function
- Clearly indicate what's not working
- Offer easy "Start All Services" option

### Performance Considerations

**Resource Usage:**
- TUI should use < 50MB RAM
- CPU usage < 5% when idle
- Don't query status more than once per second

**Log Handling:**
- When reading logs, use `tail` not reading entire file
- Limit log display to last 1000 lines
- Implement log rotation awareness

### Security Notes

**Command Injection:**
- Never pass user input directly to shell commands
- Sanitize SQL queries before sending to QuestDB
- Use subprocess with arrays, not shell=True

**File Access:**
- Only read/execute files within SPTRADER_HOME
- Don't allow arbitrary file browsing

### Testing Requirements

The TUI should be tested with:
- All services running normally
- Some services down
- No services running
- QuestDB returning errors
- Slow network conditions
- Terminal resize during operation
- Both mouse and keyboard-only navigation

### Documentation to Include

Create these files in the tui/ directory:
- `README.md` - How to use the TUI
- `ARCHITECTURE.md` - How it's built
- `KEYBINDINGS.md` - All keyboard shortcuts
- `TROUBLESHOOTING.md` - Common issues

### Exit Behavior

When user quits TUI:
- Ask "Stop all services?" (Yes/No/Cancel)
- If No: Just exit TUI, leave services running
- If Yes: Run stop_all.sh then exit
- If Cancel: Return to TUI

This ensures users don't accidentally leave services running.

## Summary

This enhanced TUI provides a complete development and operations center, combining monitoring with CI/CD capabilities for true institutional-grade efficiency. It maintains the modular architecture by delegating to existing scripts rather than reimplementing functionality.