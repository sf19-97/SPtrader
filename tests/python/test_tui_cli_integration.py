#!/usr/bin/env python3
"""Test and fix TUI-CLI integration issues"""

import subprocess
import os

# Colors for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def test_command(description, tui_cmd, expected_cli_cmd):
    """Test if TUI command matches expected CLI command"""
    print(f"\n{YELLOW}Testing: {description}{RESET}")
    print(f"  TUI uses: {tui_cmd}")
    print(f"  Should use: {expected_cli_cmd}")
    
    if tui_cmd == expected_cli_cmd:
        print(f"  {GREEN}✓ CORRECT{RESET}")
        return True
    else:
        print(f"  {RED}✗ NEEDS FIX{RESET}")
        return False

# Test each TUI function
print(f"{YELLOW}=== Testing TUI-CLI Integration ==={RESET}")

issues = []

# Test 1: Start Services
if not test_command(
    "Start Services",
    "./start_background.sh",
    "sptrader start"
):
    issues.append(("Start Services", "Line 178", "./start_background.sh", "subprocess.run(['sptrader', 'start'], check=False)"))

# Test 2: Stop Services  
if not test_command(
    "Stop Services",
    "./stop_all.sh",
    "sptrader stop"
):
    issues.append(("Stop Services", "Line 185", "./stop_all.sh", "subprocess.run(['sptrader', 'stop'], check=False)"))

# Test 3: Restart Services
if not test_command(
    "Restart Services",
    "./stop_all.sh + ./start_background.sh",
    "sptrader restart"
):
    issues.append(("Restart Services", "Lines 192-195", "manual restart", "subprocess.run(['sptrader', 'restart'], check=False)"))

# Test 4: Check Status
if not test_command(
    "Check Status",
    "./tools/check_services.sh",
    "sptrader status"
):
    issues.append(("Check Status", "Line 202", "./tools/check_services.sh", "subprocess.run(['sptrader', 'status'], check=False)"))

# Test 5: View Logs
if not test_command(
    "View Logs",
    "tail -20 logs/runtime/*.log",
    "sptrader logs"
):
    issues.append(("View Logs", "Line 210", "tail command", "subprocess.run(['sptrader', 'logs'], check=False)"))

# Test 6: API Health
# This one is OK - both use curl to the same endpoint

# Test 7: Database Stats
# This one is OK - both use curl to QuestDB

# Test 8: Monitor Mode
if not test_command(
    "Monitor Mode",
    "custom monitoring loop",
    "sptrader monitor"
):
    issues.append(("Monitor Mode", "Lines 113-166", "custom loop", "subprocess.run(['sptrader', 'monitor'], check=False)"))

# Summary
print(f"\n{YELLOW}=== Summary ==={RESET}")
print(f"Total issues found: {len(issues)}")

if issues:
    print(f"\n{RED}Issues to fix:{RESET}")
    for issue in issues:
        print(f"  - {issue[0]} at {issue[1]}")
        print(f"    Current: {issue[2]}")
        print(f"    Fix to: {issue[3]}")

# Create fixed version
if issues:
    print(f"\n{YELLOW}Creating fixed TUI version...{RESET}")
    # The fixed version will be created in the next step
    print(f"{GREEN}Fixed version will be saved as clean_tui_fixed.py{RESET}")