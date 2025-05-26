#!/usr/bin/env python3
"""SPtrader TUI with seamless matrix rain transition"""

import subprocess
import time
import sys
import os
import random
import threading
import termios
import tty
from datetime import datetime

# ANSI color codes
class Colors:
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    DARK_GREEN = '\033[32m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    CLEAR = '\033[2J'
    HOME = '\033[H'

# Matrix rain characters
MATRIX_CHARS = ["ﾓ", "ｴ", "ﾔ", "ｷ", "ｵ", "ｶ", "ｹ", "ｻ", "ｽ", "ﾖ", "ﾀ", "ﾜ", "0", "1", "2", "3", "7", "8", "9", "Z"]

# Global state for matrix rain
matrix_rain_active = True
matrix_fade_level = 0  # 0 = full brightness, 10 = faded to background
rain_columns = {}
terminal_lock = threading.Lock()
redraw_needed = threading.Event()

class MatrixColumn:
    """Represents a single column of falling characters"""
    def __init__(self, x, height):
        self.x = x
        self.height = height
        self.chars = [' '] * height
        self.speed = random.uniform(0.5, 2.0)
        self.position = random.randint(-height//2, height)
        self.length = random.randint(5, 15)
        self.last_update = time.time()
        
    def update(self):
        """Update the column position"""
        current_time = time.time()
        if current_time - self.last_update > self.speed / 10:
            self.position += 1
            self.last_update = current_time
            
            # Reset when column goes off screen
            if self.position - self.length > self.height:
                self.position = random.randint(-20, -5)
                self.length = random.randint(5, 15)
                self.speed = random.uniform(0.5, 2.0)
    
    def get_char_at(self, y):
        """Get character and color at position y"""
        if self.position - self.length < y <= self.position:
            distance_from_head = self.position - y
            if distance_from_head == 0:
                # Head of the trail - adjust brightness based on fade level
                if matrix_fade_level < 5:
                    return random.choice(MATRIX_CHARS), Colors.GREEN
                else:
                    return random.choice(MATRIX_CHARS), Colors.DIM + Colors.DARK_GREEN
            else:
                # Rest of trail - fade more with fade level
                if matrix_fade_level < 3:
                    return random.choice(MATRIX_CHARS), Colors.DARK_GREEN
                else:
                    return random.choice(MATRIX_CHARS), Colors.DIM + Colors.GRAY
        return ' ', ''

def get_terminal_size():
    """Get terminal width and height"""
    try:
        import shutil
        cols, rows = shutil.get_terminal_size()
        return cols, rows
    except:
        return 80, 24

def move_cursor(x, y):
    """Move cursor to position"""
    print(f"\033[{y};{x}H", end='', flush=True)

def init_matrix_rain(width, height):
    """Initialize matrix rain columns"""
    global rain_columns
    rain_columns.clear()
    # Create columns spaced out across the screen
    for x in range(0, width, 3):
        rain_columns[x] = MatrixColumn(x, height)

def update_matrix_rain():
    """Update all matrix rain columns"""
    for column in rain_columns.values():
        column.update()

def draw_matrix_rain():
    """Draw the matrix rain effect"""
    if not matrix_rain_active:
        return
        
    width, height = get_terminal_size()
    
    # Initialize rain if needed
    if not rain_columns:
        init_matrix_rain(width, height)
    
    # Update rain positions
    update_matrix_rain()
    
    # Draw each column
    for column in rain_columns.values():
        for y in range(1, height - 1):
            char, color = column.get_char_at(y)
            if char != ' ':
                move_cursor(column.x, y)
                print(f"{color}{char}{Colors.RESET}", end='', flush=True)

def matrix_rain_thread():
    """Background thread for matrix rain animation"""
    global matrix_fade_level
    last_size = get_terminal_size()
    
    while matrix_rain_active:
        with terminal_lock:
            # Check for terminal resize
            current_size = get_terminal_size()
            if current_size != last_size:
                init_matrix_rain(*current_size)
                last_size = current_size
                redraw_needed.set()
            
            # Only redraw if menu needs refresh or regular update
            if redraw_needed.is_set() or True:  # Always update for animation
                print(Colors.HOME + Colors.CLEAR, end='', flush=True)
                draw_matrix_rain()
                redraw_needed.clear()
        
        time.sleep(0.1)

def fade_matrix_rain():
    """Gradually fade the matrix rain to background"""
    global matrix_fade_level
    for i in range(0, 10):
        matrix_fade_level = i
        time.sleep(0.1)

def draw_box(x, y, width, height, title="", transparent=True):
    """Draw a box with optional transparency"""
    # Top line
    move_cursor(x, y)
    print(f"{Colors.CYAN}┌{'─' * (width-2)}┐{Colors.RESET}", end='')
    
    if title:
        move_cursor(x + (width - len(title) - 4) // 2, y)
        print(f"{Colors.CYAN}[ {Colors.YELLOW}{title}{Colors.CYAN} ]{Colors.RESET}", end='')
    
    # Sides
    for i in range(1, height-1):
        move_cursor(x, y+i)
        print(f"{Colors.CYAN}│{Colors.RESET}", end='')
        if not transparent:
            print(' ' * (width-2), end='')
        move_cursor(x+width-1, y+i)
        print(f"{Colors.CYAN}│{Colors.RESET}", end='')
    
    # Bottom line
    move_cursor(x, y+height-1)
    print(f"{Colors.CYAN}└{'─' * (width-2)}┘{Colors.RESET}", end='')

def show_menu():
    """Display the main menu over matrix rain"""
    width, height = get_terminal_size()
    
    menu_width = 60
    menu_height = 18
    menu_x = (width - menu_width) // 2
    menu_y = max(5, (height - menu_height) // 2)
    
    # Draw box
    draw_box(menu_x, menu_y, menu_width, menu_height, "SPTRADER CONTROL CENTER", transparent=True)
    
    # Menu items
    menu_items = [
        ("1", "Initialize Systems", Colors.GREEN),
        ("2", "Terminate Systems", Colors.RED),
        ("3", "Restart Systems", Colors.YELLOW),
        ("4", "System Status", Colors.BLUE),
        ("5", "View Logs", Colors.MAGENTA),
        ("6", "API Health", Colors.CYAN),
        ("7", "Database Stats", Colors.GREEN),
        ("M", "Monitor Mode", Colors.YELLOW),
        ("Q", "Exit", Colors.RED),
    ]
    
    y_offset = menu_y + 3
    for key, label, color in menu_items:
        move_cursor(menu_x + 5, y_offset)
        print(f"{color}[{key}]{Colors.RESET} {label}", end='')
        y_offset += 1.5
    
    # Status line
    move_cursor(menu_x + 2, menu_y + menu_height - 2)
    print(f"{Colors.DIM}Ready for input...{Colors.RESET}", end='')
    
    # Move cursor to bottom for input
    move_cursor(1, height-1)
    print(f"{Colors.GREEN}sptrader>{Colors.RESET} ", end='', flush=True)

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"

def monitor_mode():
    """Monitoring mode with matrix rain in background"""
    global matrix_fade_level
    old_fade = matrix_fade_level
    matrix_fade_level = 8  # Very faded for monitor mode
    
    while True:
        width, height = get_terminal_size()
        
        # Monitor box
        mon_width = min(width - 10, 80)
        mon_height = min(height - 6, 20)
        mon_x = (width - mon_width) // 2
        mon_y = 3
        
        with terminal_lock:
            # Clear and draw
            redraw_needed.set()
            time.sleep(0.1)  # Let matrix redraw
            
            draw_box(mon_x, mon_y, mon_width, mon_height, "SYSTEM MONITOR", transparent=False)
            
            # Time
            move_cursor(mon_x + 2, mon_y + 2)
            print(f"{Colors.YELLOW}Time:{Colors.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", end='')
            
            # Services
            move_cursor(mon_x + 2, mon_y + 4)
            print(f"{Colors.CYAN}Services:{Colors.RESET}", end='')
            
            services = [
                ("QuestDB", "pgrep -f 'questdb.*ServerMain'"),
                ("FastAPI", "pgrep -f 'uvicorn.*main:app'"),
                ("Oanda Feed", "pgrep -f 'oanda_feed.py'"),
                ("OHLC Manager", "pgrep -f 'ohlc_manager.py'")
            ]
            
            y_offset = mon_y + 6
            for name, cmd in services:
                pid = run_command(cmd).strip()
                status = f"{Colors.GREEN}● Running{Colors.RESET}" if pid else f"{Colors.RED}○ Stopped{Colors.RESET}"
                move_cursor(mon_x + 4, y_offset)
                print(f"{name:<15} {status}", end='')
                y_offset += 1
            
            # Exit instruction
            move_cursor(mon_x + 2, mon_y + mon_height - 2)
            print(f"{Colors.DIM}Press 'q' to return to menu{Colors.RESET}", end='')
        
        # Check for input
        move_cursor(1, height-1)
        print(f"{Colors.GREEN}monitor>{Colors.RESET} ", end='', flush=True)
        
        # Non-blocking input check
        import select
        if sys.stdin in select.select([sys.stdin], [], [], 5)[0]:
            key = sys.stdin.read(1)
            if key.lower() == 'q':
                matrix_fade_level = old_fade
                break

def execute_command(choice):
    """Execute menu commands"""
    width, height = get_terminal_size()
    
    # Clear area for output
    output_y = height // 2 - 5
    output_height = 10
    
    with terminal_lock:
        for y in range(output_y, output_y + output_height):
            move_cursor(1, y)
            print(' ' * width, end='')
    
    move_cursor(5, output_y + 2)
    
    if choice == '1':
        print(f"{Colors.GREEN}Starting all services...{Colors.RESET}")
        move_cursor(5, output_y + 4)
        os.system('./start_background.sh')
        
    elif choice == '2':
        print(f"{Colors.RED}Stopping all services...{Colors.RESET}")
        move_cursor(5, output_y + 4)
        os.system('./stop_all.sh')
        
    elif choice == '3':
        print(f"{Colors.YELLOW}Restarting services...{Colors.RESET}")
        move_cursor(5, output_y + 4)
        os.system('./stop_all.sh')
        time.sleep(2)
        os.system('./start_background.sh')
        
    elif choice == '4':
        os.system('./tools/check_services.sh')
        
    elif choice == '5':
        os.system('tail -20 logs/runtime/*.log | head -20')
        
    elif choice == '6':
        result = run_command("curl -s http://localhost:8000/api/health")
        print(result[:200])  # Truncate for display
        
    elif choice == '7':
        result = run_command('curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT count(*) FROM ohlc_5m_v2"')
        print(result[:200])
    
    move_cursor(1, height-1)
    input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

def main():
    """Main TUI loop with matrix rain"""
    global matrix_rain_active, matrix_fade_level
    
    # Change to SPtrader directory
    SPTRADER_HOME = os.path.expanduser("~/SPtrader")
    os.chdir(SPTRADER_HOME)
    
    # Save terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # Set terminal to raw mode for better control
        tty.setraw(sys.stdin.fileno())
        
        # Clear screen and hide cursor
        print(Colors.CLEAR + Colors.HOME + '\033[?25l', end='', flush=True)
        
        # Start matrix rain thread
        rain_thread = threading.Thread(target=matrix_rain_thread, daemon=True)
        rain_thread.start()
        
        # Fade matrix rain after a moment
        fade_thread = threading.Thread(target=fade_matrix_rain, daemon=True)
        fade_thread.start()
        
        time.sleep(0.5)  # Let rain establish
        
        while True:
            with terminal_lock:
                redraw_needed.set()
                show_menu()
            
            # Get input
            choice = sys.stdin.read(1).upper()
            
            if choice == 'Q':
                # Fade out and exit
                matrix_fade_level = 10
                time.sleep(0.5)
                break
            elif choice == 'M':
                monitor_mode()
            elif choice in '1234567':
                execute_command(choice)
            
            # Redraw menu
            redraw_needed.set()
    
    finally:
        # Restore terminal
        matrix_rain_active = False
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print('\033[?25h' + Colors.CLEAR + Colors.RESET, end='', flush=True)  # Show cursor, clear screen

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Interrupted.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")