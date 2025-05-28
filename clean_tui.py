#!/usr/bin/env python3
"""SPtrader Control Center - Clean and Simple"""

import subprocess
import time
import sys
import os
from datetime import datetime, timedelta, timezone
import json

# ANSI color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    PURPLE = '\033[95m'  # Same as magenta
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

def clear_screen():
    os.system('clear')

def get_terminal_size():
    """Get terminal width and height"""
    try:
        import shutil
        cols, rows = shutil.get_terminal_size()
        return cols, rows
    except:
        return 80, 24

def center_text(text, width):
    """Center text within given width"""
    return text.center(width)

def print_at(x, y, text, color=""):
    """Print text at specific position"""
    print(f"\033[{y};{x}H{color}{text}{Colors.RESET}", end='')
    sys.stdout.flush()

def draw_box(x, y, width, height, title="", color=Colors.CYAN):
    """Draw a simple box with optional title"""
    # Top line
    print_at(x, y, f"{color}┌{'─' * (width-2)}┐{Colors.RESET}")
    
    # Title if provided
    if title:
        title_pos = x + (width - len(title)) // 2
        print_at(title_pos, y, f"{Colors.CYAN}[ {title} ]{Colors.RESET}")
    
    # Sides
    for i in range(1, height-1):
        print_at(x, y+i, f"{color}│{' ' * (width-2)}│{Colors.RESET}")
    
    # Bottom
    print_at(x, y+height-1, f"{color}└{'─' * (width-2)}┘{Colors.RESET}")

def show_header():
    """Display simple header"""
    width, _ = get_terminal_size()
    print(Colors.CYAN + "═" * width + Colors.RESET)
    print(center_text(f"{Colors.BOLD}{Colors.GREEN}SPTRADER CONTROL CENTER{Colors.RESET}", width + 20))
    print(center_text(f"{Colors.YELLOW}[ FOREX TRADING PLATFORM ]{Colors.RESET}", width + 10))
    print(Colors.CYAN + "═" * width + Colors.RESET)

def show_menu():
    """Display the main menu"""
    width, height = get_terminal_size()
    
    # Draw main menu box
    menu_width = 50
    menu_height = 17
    menu_x = (width - menu_width) // 2
    menu_y = 8
    
    draw_box(menu_x, menu_y, menu_width, menu_height, "MAIN MENU", Colors.GREEN)
    
    # Menu items
    menu_items = [
        (f"{Colors.GREEN}[1]{Colors.RESET} Start All Services", "start"),
        (f"{Colors.RED}[2]{Colors.RESET} Stop All Services", "stop"),
        (f"{Colors.YELLOW}[3]{Colors.RESET} Restart Services", "restart"),
        (f"{Colors.BLUE}[4]{Colors.RESET} Check Status", "status"),
        (f"{Colors.MAGENTA}[5]{Colors.RESET} View Logs", "logs"),
        (f"{Colors.CYAN}[6]{Colors.RESET} API Health", "api"),
        (f"{Colors.GREEN}[7]{Colors.RESET} Database Stats", "db"),
        (f"{Colors.BLUE}[8]{Colors.RESET} Load Historical Data", "data"),
        (f"{Colors.PURPLE}[9]{Colors.RESET} Data Gap Analysis", "gaps"),
        (f"{Colors.YELLOW}[M]{Colors.RESET} Monitor Mode", "monitor"),
        (f"{Colors.RED}[Q]{Colors.RESET} Quit", "quit"),
    ]
    
    # Display menu items
    y_offset = menu_y + 3
    for item, _ in menu_items:
        print_at(menu_x + 5, y_offset, item)
        y_offset += 1
    
    # Time display
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_at(width - 25, height - 2, f"{Colors.GREEN}[{current_time}]{Colors.RESET}")

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else f"{Colors.RED}Error: {result.stderr}{Colors.RESET}"
    except Exception as e:
        return f"{Colors.RED}Error: {str(e)}{Colors.RESET}"

def monitor_mode():
    """Simple monitoring display"""
    while True:
        clear_screen()
        width, height = get_terminal_size()
        
        # Monitor header
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.GREEN}SYSTEM MONITOR{Colors.RESET}", width + 20))
        print(Colors.GREEN + "═" * width + Colors.RESET)
        
        # Time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{Colors.YELLOW}Timestamp:{Colors.RESET} {current_time}")
        print(f"{Colors.CYAN}Press Ctrl+C to return to menu{Colors.RESET}")
        print(Colors.DIM + "─" * width + Colors.RESET)
        
        # Service status
        print(f"\n{Colors.BOLD}{Colors.CYAN}SERVICE STATUS:{Colors.RESET}")
        
        services = [
            ("QuestDB", "pgrep -f 'questdb.*ServerMain'", "9000"),
            ("Go API", "pgrep -f .sptrader-api.", "8000"),
            ("Oanda Feed", "pgrep -f 'oanda_feed.py'", "N/A"),
            ("OHLC Manager", "pgrep -f 'ohlc_manager.py'", "N/A")
        ]
        
        for name, cmd, port in services:
            pid = run_command(cmd).strip()
            if pid and not pid.startswith("Error"):
                status = f"{Colors.GREEN}● ONLINE{Colors.RESET}"
                pid_info = f"PID: {pid.split()[0]}" if pid else ""
            else:
                status = f"{Colors.RED}○ OFFLINE{Colors.RESET}"
                pid_info = ""
            
            print(f"  {name:<15} {status:<20} {pid_info:<15} PORT: {port}")
        
        # API Health
        print(f"\n{Colors.BOLD}{Colors.CYAN}API STATUS:{Colors.RESET}")
        health = run_command("curl -s http://localhost:8080/api/v1/health 2>/dev/null")
        if "healthy" in health.lower():
            api_status = f"{Colors.GREEN}● API OPERATIONAL{Colors.RESET}"
        else:
            api_status = f"{Colors.RED}○ API UNREACHABLE{Colors.RESET}"
        print(f"  {api_status}")
        
        print(Colors.DIM + "─" * width + Colors.RESET)
        print("Refreshing every 5 seconds...")
        
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            break

def execute_command(choice):
    """Execute commands"""
    clear_screen()
    width, _ = get_terminal_size()
    
    if choice == '1':
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.GREEN}STARTING SERVICES{Colors.RESET}", width + 20))
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print()
        os.system('./sptrader start')
        
    elif choice == '2':
        print(Colors.RED + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.RED}STOPPING SERVICES{Colors.RESET}", width + 20))
        print(Colors.RED + "═" * width + Colors.RESET)
        print()
        os.system('./sptrader stop')
        
    elif choice == '3':
        print(Colors.YELLOW + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.YELLOW}RESTARTING SERVICES{Colors.RESET}", width + 20))
        print(Colors.YELLOW + "═" * width + Colors.RESET)
        print()
        os.system('./sptrader restart')
        
    elif choice == '4':
        print(Colors.BLUE + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.BLUE}SYSTEM STATUS{Colors.RESET}", width + 20))
        print(Colors.BLUE + "═" * width + Colors.RESET)
        print()
        os.system('./sptrader status')
        
    elif choice == '5':
        print(Colors.MAGENTA + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.MAGENTA}SYSTEM LOGS{Colors.RESET}", width + 20))
        print(Colors.MAGENTA + "═" * width + Colors.RESET)
        print()
        print(f"{Colors.CYAN}Recent log entries:{Colors.RESET}")
        os.system('tail -20 logs/runtime/*.log | grep -v "^$" | tail -20')
        
    elif choice == '6':
        print(Colors.CYAN + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.CYAN}API HEALTH CHECK{Colors.RESET}", width + 20))
        print(Colors.CYAN + "═" * width + Colors.RESET)
        print()
        result = run_command("curl -s http://localhost:8080/api/v1/health | python3 -m json.tool")
        print(result)
        
    elif choice == '7':
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.GREEN}DATABASE STATISTICS{Colors.RESET}", width + 20))
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print()
        result = run_command('curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT count(*) FROM ohlc_5m_v2" 2>/dev/null')
        print(f"{Colors.CYAN}Query Result:{Colors.RESET}")
        print(result)
    
    elif choice == '8':
        load_historical_data()
    
    elif choice == '9':
        print(Colors.PURPLE + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.PURPLE}DATA GAP ANALYSIS{Colors.RESET}", width + 20))
        print(Colors.PURPLE + "═" * width + Colors.RESET)
        print()
        os.system('./sptrader db gaps --fill')
    
    print()
    print(Colors.DIM + "─" * width + Colors.RESET)
    input(f"{Colors.YELLOW}Press ENTER to return to menu...{Colors.RESET}")

def load_historical_data():
    """Interactive data loading menu"""
    clear_screen()
    width, _ = get_terminal_size()
    
    print(Colors.BLUE + "═" * width + Colors.RESET)
    print(center_text(f"{Colors.BOLD}{Colors.BLUE}HISTORICAL DATA LOADER{Colors.RESET}", width + 20))
    print(Colors.BLUE + "═" * width + Colors.RESET)
    print()
    
    # First, check what data we already have
    print(f"{Colors.CYAN}Checking existing data...{Colors.RESET}")
    query_result = run_command("""
        curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT symbol, min(timestamp) as first_tick, max(timestamp) as last_tick, count(*) as tick_count FROM market_data_v2 GROUP BY symbol" 2>/dev/null
    """)
    
    existing_symbols = {}
    try:
        data = json.loads(query_result)
        if "dataset" in data:
            print(f"\n{Colors.GREEN}Current data in database:{Colors.RESET}")
            print(f"     {'Symbol':<10} {'First Date':<20} {'Last Date':<20} {'Tick Count':>15}")
            print("     " + "-" * 65)
            
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            # Sort by symbol name for consistent ordering
            sorted_data = sorted(data["dataset"], key=lambda x: x[0])
            for idx, row in enumerate(sorted_data):
                letter = letters[idx] if idx < len(letters) else str(idx)
                symbol = row[0]
                existing_symbols[letter] = {
                    'symbol': symbol,
                    'first': row[1],
                    'last': row[2],
                    'count': row[3]
                }
                first = datetime.fromisoformat(row[1].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                last = datetime.fromisoformat(row[2].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                count = f"{row[3]:,}"
                print(f"{Colors.CYAN}[{letter}]{Colors.RESET}  {symbol:<10} {first:<20} {last:<20} {count:>15}")
    except:
        print(f"{Colors.YELLOW}No existing data found or couldn't parse response{Colors.RESET}")
    
    print(f"\n{Colors.CYAN}Select loading option:{Colors.RESET}")
    print(f"  {Colors.GREEN}[1]{Colors.RESET} Fill from last date to today")
    print(f"  {Colors.GREEN}[2]{Colors.RESET} Fill backwards from first date")
    print(f"  {Colors.GREEN}[3]{Colors.RESET} Load specific date range")
    print(f"  {Colors.GREEN}[4]{Colors.RESET} Load last 30 days")
    print(f"  {Colors.GREEN}[5]{Colors.RESET} Load last 90 days")
    print(f"  {Colors.GREEN}[6]{Colors.RESET} Load full year (365 days)")
    print(f"  {Colors.RED}[C]{Colors.RESET} Cancel")
    
    option = input(f"\n{Colors.YELLOW}Select option: {Colors.RESET}").strip()
    
    if option.upper() == 'C':
        return
    
    # Select symbols
    print(f"\n{Colors.CYAN}Select symbols to load:{Colors.RESET}")
    if existing_symbols:
        print(f"  Enter letter(s) from above (e.g., A or A,B,C)")
        print(f"  Or use:")
    print(f"  {Colors.GREEN}[ALL]{Colors.RESET} All existing symbols")
    print(f"  {Colors.GREEN}[NEW]{Colors.RESET} Enter new symbol manually")
    
    symbol_choice = input(f"\n{Colors.YELLOW}Select symbols: {Colors.RESET}").strip().upper()
    
    symbols = []
    if symbol_choice == 'ALL':
        symbols = [info['symbol'] for info in existing_symbols.values()]
    elif symbol_choice == 'NEW':
        custom = input(f"{Colors.YELLOW}Enter symbols (comma-separated): {Colors.RESET}")
        symbols = [s.strip().upper() for s in custom.split(',')]
    else:
        # Parse letter selections
        letters = [l.strip() for l in symbol_choice.split(',')]
        for letter in letters:
            if letter in existing_symbols:
                symbols.append(existing_symbols[letter]['symbol'])
            else:
                print(f"{Colors.RED}Invalid selection: {letter}{Colors.RESET}")
                return
    
    if not symbols:
        print(f"{Colors.RED}No symbols selected{Colors.RESET}")
        return
    
    # Determine date range based on option
    end_date = datetime.now(timezone.utc)
    start_date = None
    
    if option == '1':
        # Fill from last to today - need to get last date from DB
        # Use the earliest "last date" among selected symbols
        latest_dates = []
        for symbol in symbols:
            # Check if we have existing data for this symbol
            for letter, info in existing_symbols.items():
                if info['symbol'] == symbol:
                    try:
                        last_date = datetime.fromisoformat(info['last'].replace('Z', '+00:00'))
                        latest_dates.append(last_date)
                    except:
                        pass
        
        if latest_dates:
            # Start from the earliest "last date" + 1 day
            start_date = min(latest_dates) + timedelta(days=1)
        else:
            # No existing data, default to last 30 days
            start_date = end_date - timedelta(days=30)
            
    elif option == '2':
        # Fill backwards from first date
        # Use the latest "first date" among selected symbols
        first_dates = []
        for symbol in symbols:
            # Check if we have existing data for this symbol
            for letter, info in existing_symbols.items():
                if info['symbol'] == symbol:
                    try:
                        first_date = datetime.fromisoformat(info['first'].replace('Z', '+00:00'))
                        first_dates.append(first_date)
                    except:
                        pass
        
        if first_dates:
            # End one day before the latest "first date"
            end_date = max(first_dates) - timedelta(days=1)
            start_date = end_date - timedelta(days=90)  # Load 90 days before
        else:
            # No existing data, default to last 30 days
            start_date = end_date - timedelta(days=30)
            
    elif option == '3':
        # Custom date range
        start_str = input(f"{Colors.YELLOW}Enter start date (YYYY-MM-DD): {Colors.RESET}")
        end_str = input(f"{Colors.YELLOW}Enter end date (YYYY-MM-DD): {Colors.RESET}")
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
        except:
            print(f"{Colors.RED}Invalid date format{Colors.RESET}")
            return
            
    elif option == '4':
        start_date = end_date - timedelta(days=30)
    elif option == '5':
        start_date = end_date - timedelta(days=90)
    elif option == '6':
        start_date = end_date - timedelta(days=365)
    else:
        print(f"{Colors.RED}Invalid option{Colors.RESET}")
        return
    
    # Confirm before loading
    print(f"\n{Colors.YELLOW}Ready to load data:{Colors.RESET}")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Start: {start_date.strftime('%Y-%m-%d')}")
    print(f"  End: {end_date.strftime('%Y-%m-%d')}")
    try:
        days_diff = (end_date.date() - start_date.date()).days
        print(f"  Days: {days_diff}")
    except:
        print(f"  Days: calculating...")
    
    confirm = input(f"\n{Colors.YELLOW}Proceed? (y/N): {Colors.RESET}").strip().lower()
    if confirm != 'y':
        print(f"{Colors.RED}Cancelled{Colors.RESET}")
        return
    
    # Load data for each symbol
    print(f"\n{Colors.GREEN}Loading data...{Colors.RESET}")
    os.chdir(os.path.expanduser("~/SPtrader/data_feeds"))
    
    for symbol in symbols:
        print(f"\n{Colors.CYAN}Loading {symbol}...{Colors.RESET}")
        cmd = f"python3 dukascopy_to_ilp.py {symbol} {start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"
        result = os.system(cmd)
        if result == 0:
            print(f"{Colors.GREEN}✓ {symbol} loaded successfully{Colors.RESET}")
        else:
            print(f"{Colors.RED}✗ {symbol} failed to load{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}Data loading complete!{Colors.RESET}")
    os.chdir(os.path.expanduser("~/SPtrader"))

def main():
    """Main loop"""
    SPTRADER_HOME = os.path.expanduser("~/SPtrader")
    os.chdir(SPTRADER_HOME)
    
    while True:
        clear_screen()
        show_header()
        show_menu()
        
        # Input prompt
        width, height = get_terminal_size()
        print_at(1, height-1, f"{Colors.GREEN}sptrader>{Colors.RESET} ")
        
        choice = input().strip().upper()
        
        if choice == 'M':
            monitor_mode()
        elif choice == 'Q':
            clear_screen()
            print(f"\n{Colors.GREEN}Goodbye!{Colors.RESET}\n")
            sys.exit(0)
        elif choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
            execute_command(choice)
        else:
            print(f"\n{Colors.RED}Invalid input. Try again.{Colors.RESET}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Interrupted. Exiting...{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(1)