def init_matrix_rain(width, height):
    """Initialize matrix rain columns"""
    global rain_columns
    rain_columns.clear()  # Clear any existing columns
    # Create columns spaced out across the screen
    for x in range(2, width, 6):  # Every 6 characters for very sparse rain
        rain_columns[x] = MatrixColumn(x, height)

def update_matrix_rain():
    """Update all matrix rain columns"""
    for column in rain_columns.values():
        column.update()

def draw_matrix_rain_background():
    """Draw the matrix rain effect in background"""
    if not matrix_rain_active:
        return
        
    width, height = get_terminal_size()
    
    # Initialize rain if needed
    if not rain_columns:
        init_matrix_rain(width, height)
    
    # Update rain positions
    update_matrix_rain()
    
    # Draw each column
    with terminal_lock:
        for column in rain_columns.values():
            for y in range(1, height - 1):
                char, color = column.get_char_at(y)
                if char != ' ':
                    try:
                        print_at(column.x, y, char, color)
                    except:
                        pass

def matrix_rain_thread():
    """Background thread for matrix rain animation"""
    while matrix_rain_active:
        time.sleep(0.15)  # Update every 150ms for slower, smoother rain#!/usr/bin/env python3
"""SPtrader Control Center - Cyberpunk Edition with Matrix Rain"""

import subprocess
import time
import sys
import os
import random
import threading
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
    DARK_GREEN = '\033[32m'  # Darker green for rain
    
    # Bright versions
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    
    # Background
    BG_BLACK = '\033[40m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'
    BG_GRAY = '\033[100m'
    
    # Special
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    RESET = '\033[0m'
    CLEAR_LINE = '\033[K'

# Matrix rain characters for decoration
MATRIX_CHARS = ["ﾓ", "ｴ", "ﾔ", "ｷ", "ｵ", "ｶ", "ｹ", "ｻ", "ｽ", "ﾖ", "ﾀ", "ﾜ", "0", "1", "2", "3", "7", "8", "9", "Z"]

# Global variables for matrix rain
matrix_rain_active = True
rain_columns = {}
terminal_lock = threading.Lock()

class MatrixColumn:
    """Represents a single column of falling characters"""
    def __init__(self, x, height):
        self.x = x
        self.height = height
        self.chars = [' '] * height
        self.length = random.randint(2, 7)  # Even shorter trails
        self.speed = random.uniform(1.5, 4.0)  # Even slower speed
        self.position = random.randint(-height, 0)
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
                self.length = random.randint(2, 7)
                self.speed = random.uniform(1.5, 4.0)
    
    def get_char_at(self, y):
        """Get character at position y"""
        if self.position - self.length < y <= self.position:
            # Character is part of the trail
            distance_from_head = self.position - y
            if distance_from_head == 0:
                # Head of the trail - very dim green
                return random.choice(MATRIX_CHARS), Colors.DIM + Colors.DARK_GREEN
            else:
                # Rest of trail - extremely faint
                return random.choice(MATRIX_CHARS), Colors.DIM + Colors.GRAY
        return ' ', ''

# Box drawing characters
class Box:
    TL = "╔"  # Top left
    TR = "╗"  # Top right
    BL = "╚"  # Bottom left
    BR = "╝"  # Bottom right
    H = "═"   # Horizontal
    V = "║"   # Vertical
    T = "╦"   # T junction
    B = "╩"   # Bottom junction
    L = "╠"   # Left junction
    R = "╣"   # Right junction
    X = "╬"   # Cross

def clear_screen():
    os.system('clear')
    sys.stdout.flush()  # Ensure output is flushed

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

def glitch_text(text, intensity=0.1):
    """Add glitch effect to text"""
    result = ""
    for char in text:
        if random.random() < intensity and char != ' ':
            result += random.choice(MATRIX_CHARS)
        else:
            result += char
    return result

def draw_box(x, y, width, height, title="", color=Colors.GREEN):
    """Draw a box at position with optional title"""
    # Move cursor and draw top line
    print(f"\033[{y};{x}H{color}{Box.TL}{Box.H * (width-2)}{Box.TR}{Colors.RESET}")
    
    # Draw title if provided
    if title:
        title_pos = x + (width - len(title)) // 2
        print(f"\033[{y};{title_pos}H{Colors.CYAN}[ {title} ]{Colors.RESET}")
    
    # Draw sides
    for i in range(1, height-1):
        print(f"\033[{y+i};{x}H{color}{Box.V}{' ' * (width-2)}{Box.V}{Colors.RESET}")
    
    # Draw bottom
    print(f"\033[{y+height-1};{x}H{color}{Box.BL}{Box.H * (width-2)}{Box.BR}{Colors.RESET}")

def print_at(x, y, text, color=""):
    """Print text at specific position (thread-safe)"""
    # Use terminal lock if available (for matrix rain)
    if 'terminal_lock' in globals():
        with terminal_lock:
            print(f"\033[{y};{x}H{color}{text}{Colors.RESET}", end='')
            sys.stdout.flush()
    else:
        print(f"\033[{y};{x}H{color}{text}{Colors.RESET}", end='')
        sys.stdout.flush()

def animate_header():
    """Create animated header effect with trading theme"""
    width, _ = get_terminal_size()
    header_text = "SPTRADER CONTROL CENTER"
    subheader = "[ FOREX TRADING PLATFORM ]"
    
    # Glitch effect on header
    glitched = glitch_text(header_text, 0.15)
    
    # Create cyberpunk style header with trading symbols
    print(Colors.CYAN + "═" * width + Colors.RESET)
    print(center_text(f"{Colors.BOLD}{Colors.GREEN}{glitched}{Colors.RESET}", width + 20))
    print(center_text(f"{Colors.YELLOW}{subheader}{Colors.RESET}", width + 10))
    print(Colors.CYAN + "═" * width + Colors.RESET)
    
    # Add trading ticker effect
    ticker_symbols = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CHF"]
    ticker_line = " │ ".join([f"{Colors.GREEN if random.random() > 0.5 else Colors.RED}{sym}{Colors.RESET}" 
                             for sym in ticker_symbols])
    print(center_text(ticker_line, width + 50))



def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else f"{Colors.RED}Error: {result.stderr}{Colors.RESET}"
    except Exception as e:
        return f"{Colors.RED}Error: {str(e)}{Colors.RESET}"

def load_ascii_art():
    """Load Wolf of Wall Street ASCII art from file"""
    art_paths = [
        os.path.expanduser("~/SPtrader/wwstascii.txt"),
        os.path.expanduser("~/SPtrader/assets/wwstascii.txt"),
        "wwstascii.txt"
    ]
    
    for path in art_paths:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read().splitlines()
        except:
            pass
    
    # If no file found, return empty list (just use matrix rain)
    return []

def display_background_art():
    """Display Wolf of Wall Street ASCII art as background with matrix rain"""
    width, height = get_terminal_size()
    
    # First draw the matrix rain
    draw_matrix_rain_background()
    
    # Then overlay the Wolf art if it exists
    art = load_ascii_art()
    if art:  # Only display if we have art
        # Calculate scaling and positioning
        art_height = len(art)
        art_width = max(len(line) for line in art) if art else 0
        
        # Start position - try to center or show top portion
        start_y = 0
        start_x = max(0, (width - art_width) // 2) if art_width < width else 0
        
        # Display the art very dimmed
        for y, line in enumerate(art):
            if y >= height - 2:  # Leave room at bottom
                break
            
            # Truncate or pad line to fit screen
            if len(line) > width:
                display_line = line[:width]
            else:
                display_line = line
            
            # Print with very dim coloring for background effect
            try:
                print_at(start_x + 1, y + 1, display_line, Colors.DIM + Colors.GRAY)
            except:
                pass  # Skip if position is out of bounds

def draw_transparent_box(x, y, width, height, title="", color=Colors.GREEN):
    """Draw a semi-transparent box for menu overlay"""
    # Top line with title
    print_at(x, y, f"{color}┌{'─' * (width-2)}┐{Colors.RESET}")
    
    if title:
        title_text = f"[ {title} ]"
        title_pos = x + (width - len(title_text)) // 2
        print_at(title_pos, y, f"{Colors.CYAN}{Colors.BOLD}{title_text}{Colors.RESET}")
    
    # Sides with semi-transparent background
    for i in range(1, height-1):
        # Left border
        print_at(x, y+i, f"{color}│{Colors.RESET}")
        # Clear/darken the line content
        print_at(x+1, y+i, f"{Colors.BLACK}{Colors.BG_BLACK}{' ' * (width-2)}{Colors.RESET}")
        # Right border
        print_at(x+width-1, y+i, f"{color}│{Colors.RESET}")
    
    # Bottom line
    print_at(x, y+height-1, f"{color}└{'─' * (width-2)}┘{Colors.RESET}")

def show_menu():
    """Display the cyberpunk menu with matrix rain and Wolf background"""
    width, height = get_terminal_size()
    
    # First, display the background (matrix rain + optional Wolf art)
    display_background_art()
    
    # Draw main menu box with transparency
    menu_width = 65
    menu_height = 20
    menu_x = (width - menu_width) // 2
    menu_y = max(10, (height - menu_height) // 2)
    
    # Draw semi-transparent box
    draw_transparent_box(menu_x, menu_y, menu_width, menu_height, "SPTRADER COMMAND CENTER", Colors.BRIGHT_GREEN)
    
    # Menu items with cyberpunk styling
    menu_items = [
        (f"{Colors.BRIGHT_GREEN}[1]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} Initialize All Systems", "start"),
        (f"{Colors.RED}[2]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} Terminate All Systems", "stop"),
        (f"{Colors.YELLOW}[3]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} System Reboot Sequence", "restart"),
        (f"{Colors.BLUE}[4]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} System Diagnostics", "status"),
        (f"{Colors.MAGENTA}[5]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} Access System Logs", "logs"),
        (f"{Colors.GREEN}[6]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} API Neural Check", "api"),
        (f"{Colors.CYAN}[7]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} Database Matrix Stats", "db"),
        (f"{Colors.YELLOW}[M]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} {Colors.BLINK}MONITOR MODE{Colors.RESET}", "monitor"),
        (f"{Colors.RED}[Q]{Colors.RESET} {Colors.CYAN}►{Colors.RESET} Jack Out", "quit"),
    ]
    
    # Display menu items with background clearing for readability
    y_offset = menu_y + 3
    for i, (item, _) in enumerate(menu_items):
        # Clear background for this line
        print_at(menu_x + 2, y_offset + i * 1.5, 
                f"{Colors.BG_BLACK}{' ' * (menu_width-4)}{Colors.RESET}")
        # Print menu item
        print_at(menu_x + 5, y_offset + i * 1.5, item)
    
    # Status line with dark background
    print_at(menu_x + 2, menu_y + menu_height - 3,
             f"{Colors.BG_BLACK}{' ' * (menu_width-4)}{Colors.RESET}")
    print_at(menu_x + 2, menu_y + menu_height - 2, 
             f"{Colors.DIM}{'─' * (menu_width-4)}{Colors.RESET}")
    
    # "THE WOLF OF TRADING" easter egg at bottom of menu
    wolf_text = "< THE WOLF OF FOREX TRADING >"
    print_at(menu_x + (menu_width - len(wolf_text)) // 2, menu_y + menu_height - 2,
             f"{Colors.DIM}{Colors.YELLOW}{wolf_text}{Colors.RESET}")
    
    # Time display
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_at(width - 25, height - 2, f"{Colors.GREEN}[{current_time}]{Colors.RESET}")

def loading_animation(message, duration=1):
    """Show a cyberpunk loading animation"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    
    while time.time() < end_time:
        print(f"\r{Colors.CYAN}{frames[i % len(frames)]} {message}{Colors.RESET}", end='')
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    print(f"\r{Colors.GREEN}✓ {message}{Colors.RESET}")
    sys.stdout.flush()

def monitor_mode():
    """Enhanced monitoring display with matrix rain background"""
    while True:
        clear_screen()
        width, height = get_terminal_size()
        
        # Show matrix rain in background
        draw_matrix_rain_background()
        
        # Create a semi-transparent overlay for the monitor
        monitor_box_width = min(width - 4, 100)
        monitor_box_height = min(height - 4, 30)
        monitor_x = (width - monitor_box_width) // 2
        monitor_y = 2
        
        # Draw transparent box for monitor
        with terminal_lock:
            draw_transparent_box(monitor_x, monitor_y, monitor_box_width, monitor_box_height, 
                               "SYSTEM MONITOR - REAL TIME", Colors.BRIGHT_GREEN)
            
            # Clear areas for text
            for i in range(1, monitor_box_height - 1):
                print_at(monitor_x + 1, monitor_y + i, 
                        f"{Colors.BG_BLACK}{' ' * (monitor_box_width - 2)}{Colors.RESET}")
            
            # Time and system info
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print_at(monitor_x + 2, monitor_y + 2, 
                    f"{Colors.YELLOW}TIMESTAMP:{Colors.RESET} {current_time} │ {Colors.CYAN}[ESC TO EXIT]{Colors.RESET}")
            
            # Service status section
            print_at(monitor_x + 2, monitor_y + 4, f"{Colors.BOLD}{Colors.CYAN}SERVICE STATUS:{Colors.RESET}")
            print_at(monitor_x + 2, monitor_y + 5, Colors.DIM + "─" * (monitor_box_width - 4) + Colors.RESET)
            
            services = [
                ("QuestDB", "pgrep -f 'questdb.*ServerMain'", "9000"),
                ("FastAPI", "pgrep -f 'uvicorn.*main:app'", "8000"),
                ("Oanda Feed", "pgrep -f 'oanda_feed.py'", "N/A"),
                ("OHLC Manager", "pgrep -f 'ohlc_manager.py'", "N/A")
            ]
            
            y_offset = monitor_y + 7
            for name, cmd, port in services:
                pid = run_command(cmd).strip()
                if pid and not pid.startswith("Error"):
                    status = f"{Colors.BRIGHT_GREEN}● ONLINE{Colors.RESET}"
                    pid_info = f"PID: {pid.split()[0]}" if pid else ""
                    
                    # Get memory usage if running
                    if pid:
                        mem_cmd = f"ps -p {pid.split()[0]} -o rss= 2>/dev/null | awk '{{printf \"%.1f MB\", $1/1024}}'"
                        memory = run_command(mem_cmd).strip()
                        mem_info = f"MEM: {memory}" if memory else ""
                    else:
                        mem_info = ""
                else:
                    status = f"{Colors.RED}○ OFFLINE{Colors.RESET}"
                    pid_info = ""
                    mem_info = ""
                
                line = f"{name:<15} {status:<20} {pid_info:<15} {mem_info:<12} PORT: {port}"
                print_at(monitor_x + 4, y_offset, line)
                y_offset += 1
            
            # API Health section
            print_at(monitor_x + 2, y_offset + 1, f"{Colors.BOLD}{Colors.CYAN}API STATUS:{Colors.RESET}")
            print_at(monitor_x + 2, y_offset + 2, Colors.DIM + "─" * (monitor_box_width - 4) + Colors.RESET)
            
            health = run_command("curl -s http://localhost:8000/api/health 2>/dev/null")
            if "healthy" in health.lower():
                api_status = f"{Colors.BRIGHT_GREEN}● API OPERATIONAL{Colors.RESET}"
            else:
                api_status = f"{Colors.RED}○ API UNREACHABLE{Colors.RESET}"
            
            print_at(monitor_x + 4, y_offset + 3, api_status)
            
            # Market data section
            print_at(monitor_x + 2, y_offset + 5, f"{Colors.BOLD}{Colors.CYAN}MARKET DATA STREAM:{Colors.RESET}")
            print_at(monitor_x + 2, y_offset + 6, Colors.DIM + "─" * (monitor_box_width - 4) + Colors.RESET)
            
            # Simulate market data
            pairs = ["EUR/USD", "GBP/USD", "USD/JPY"]
            y_offset += 8
            for pair in pairs:
                bid = 1.0000 + random.random() * 0.1
                ask = bid + 0.0001
                change = random.choice(["▲", "▼"])
                color = Colors.GREEN if change == "▲" else Colors.RED
                
                line = f"{pair:<10} BID: {bid:.5f}  ASK: {ask:.5f}  {color}{change}{Colors.RESET}"
                print_at(monitor_x + 4, y_offset, line)
                y_offset += 1
            
            # Bottom status
            status_line = f"Refresh: 5s │ CPU: {random.randint(10,40)}% │ Connections: {random.randint(5,20)}"
            print_at(monitor_x + (monitor_box_width - len(status_line)) // 2, 
                    monitor_y + monitor_box_height - 2, 
                    f"{Colors.DIM}{status_line}{Colors.RESET}")
        
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            break

def execute_with_style(choice):
    """Execute commands with cyberpunk flair"""
    clear_screen()
    width, _ = get_terminal_size()
    
    if choice == '1':
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.GREEN}SYSTEM INITIALIZATION SEQUENCE{Colors.RESET}", width + 30))
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print()
        
        loading_animation("Initializing quantum cores", 0.8)
        loading_animation("Establishing neural links", 0.6)
        loading_animation("Calibrating data streams", 0.7)
        print()
        
        print(f"{Colors.CYAN}Executing: {Colors.YELLOW}./start_background.sh{Colors.RESET}")
        print(Colors.DIM + "─" * width + Colors.RESET)
        os.system('./start_background.sh')
        
    elif choice == '2':
        print(Colors.RED + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.RED}SYSTEM TERMINATION PROTOCOL{Colors.RESET}", width + 30))
        print(Colors.RED + "═" * width + Colors.RESET)
        print()
        
        print(f"{Colors.RED}⚠  WARNING: All systems will be terminated ⚠{Colors.RESET}")
        loading_animation("Shutting down neural networks", 1)
        print()
        
        os.system('./stop_all.sh')
        
    elif choice == '3':
        print(Colors.YELLOW + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.YELLOW}SYSTEM REBOOT SEQUENCE{Colors.RESET}", width + 30))
        print(Colors.YELLOW + "═" * width + Colors.RESET)
        print()
        
        loading_animation("Terminating current processes", 0.8)
        os.system('./stop_all.sh')
        
        loading_animation("Cooling down cores", 1.5)
        time.sleep(1.5)
        
        loading_animation("Reinitializing systems", 0.8)
        os.system('./start_background.sh')
        
    elif choice == '4':
        print(Colors.BLUE + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.BLUE}SYSTEM DIAGNOSTICS{Colors.RESET}", width + 30))
        print(Colors.BLUE + "═" * width + Colors.RESET)
        print()
        
        loading_animation("Scanning system matrix", 0.5)
        print()
        os.system('./tools/check_services.sh')
        
    elif choice == '5':
        print(Colors.MAGENTA + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.MAGENTA}ACCESSING SYSTEM LOGS{Colors.RESET}", width + 30))
        print(Colors.MAGENTA + "═" * width + Colors.RESET)
        print()
        
        loading_animation("Decrypting log streams", 0.4)
        print()
        print(f"{Colors.CYAN}Recent log entries:{Colors.RESET}")
        print(Colors.DIM + "─" * width + Colors.RESET)
        os.system('tail -20 logs/runtime/*.log | grep -v "^$" | tail -20')
        
    elif choice == '6':
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.GREEN}API NEURAL CHECK{Colors.RESET}", width + 30))
        print(Colors.GREEN + "═" * width + Colors.RESET)
        print()
        
        loading_animation("Establishing API connection", 0.3)
        print()
        result = run_command("curl -s http://localhost:8000/api/health | python3 -m json.tool")
        print(result)
        
    elif choice == '7':
        print(Colors.CYAN + "═" * width + Colors.RESET)
        print(center_text(f"{Colors.BOLD}{Colors.CYAN}DATABASE MATRIX STATISTICS{Colors.RESET}", width + 30))
        print(Colors.CYAN + "═" * width + Colors.RESET)
        print()
        
        loading_animation("Querying temporal database", 0.5)
        print()
        result = run_command('curl -s -G "http://localhost:9000/exec" --data-urlencode "query=SELECT count(*) FROM ohlc_5m_v2" 2>/dev/null')
        print(f"{Colors.CYAN}Query Result:{Colors.RESET}")
        print(result)
    
    print()
    print(Colors.DIM + "─" * width + Colors.RESET)
    input(f"{Colors.YELLOW}Press ENTER to return to main interface...{Colors.RESET}")

def show_wolf_splash():
    """Show Wolf of Wall Street splash screen with matrix rain"""
    clear_screen()
    width, height = get_terminal_size()
    
    # Initialize matrix rain for splash (but it won't show immediately)
    init_matrix_rain(width, height)
    
    # Show Wolf art first without rain for 1 second
    art = load_ascii_art()
    if art:
        art_height = len(art)
        art_width = max(len(line) for line in art) if art else 0
        start_y = 0
        start_x = max(0, (width - art_width) // 2) if art_width < width else 0
        
        for y, line in enumerate(art):
            if y >= height - 2:
                break
            if len(line) > width:
                display_line = line[:width]
            else:
                display_line = line
            try:
                print_at(start_x + 1, y + 1, display_line, Colors.DIM + Colors.GRAY)
            except:
                pass
    
    # Add title
    title_lines = [
        "╔═══════════════════════════════════════╗",
        "║       SPTRADER TRADING PLATFORM       ║",
        "║    'THE WOLF OF FOREX TRADING'        ║",
        "╚═══════════════════════════════════════╝"
    ]
    
    title_y = height - 8
    for i, line in enumerate(title_lines):
        x_pos = (width - len(line)) // 2
        print_at(x_pos - 1, title_y + i, f"{Colors.BG_BLACK}{' ' * (len(line) + 2)}{Colors.RESET}")
        print_at(x_pos, title_y + i, line, Colors.YELLOW + Colors.BOLD)
    
    time.sleep(1)  # Show just the art first
    
    # Then show animated splash with rain for 2 seconds
    start_time = time.time()
    while time.time() - start_time < 2:
        clear_screen()
        
        # Display the matrix rain + art
        display_background_art()
        
        # Re-add title text over the art
        for i, line in enumerate(title_lines):
            x_pos = (width - len(line)) // 2
            print_at(x_pos - 1, title_y + i, f"{Colors.BG_BLACK}{' ' * (len(line) + 2)}{Colors.RESET}")
            print_at(x_pos, title_y + i, line, Colors.YELLOW + Colors.BOLD)
        
        # Loading message
        loading_text = "Initializing Trading Systems..."
        loading_x = (width - len(loading_text)) // 2
        print_at(loading_x - 1, height - 3, f"{Colors.BG_BLACK}{' ' * (len(loading_text) + 2)}{Colors.RESET}")
        print_at(loading_x, height - 3, f"{Colors.GREEN}{loading_text}{Colors.RESET}")
        
        time.sleep(0.1)
    
    # Brief loading animation
    loading_animation("Loading market data", 0.5)
    loading_animation("Establishing connections", 0.5)
    
def main():
    """Main loop with cyberpunk aesthetics and matrix rain"""
    global matrix_rain_active
    
    SPTRADER_HOME = os.path.expanduser("~/SPtrader")
    os.chdir(SPTRADER_HOME)
    
    # Show Wolf of Wall Street splash first (without rain initially)
    show_wolf_splash()
    
    # Now start matrix rain animation thread after splash
    rain_thread = threading.Thread(target=matrix_rain_thread, daemon=True)
    rain_thread.start()
    
    try:
        while True:
            clear_screen()
            animate_header()
            show_menu()
            
            # Cyberpunk input prompt
            width, height = get_terminal_size()
            with terminal_lock:
                print_at(1, height-1, f"{Colors.GREEN}root@sptrader:~#{Colors.RESET} ", Colors.BOLD)
            
            choice = input().strip().upper()
            
            if choice == 'M':
                monitor_mode()
            elif choice == 'Q':
                matrix_rain_active = False  # Stop the rain
                clear_screen()
                # Show the matrix rain one more time on exit
                display_background_art()
                width, height = get_terminal_size()
                print_at((width - 40) // 2, height // 2, 
                        f"{Colors.GREEN}{glitch_text('DISCONNECTING FROM TRADING MATRIX...', 0.3)}{Colors.RESET}")
                time.sleep(1)
                print_at((width - 30) // 2, height // 2 + 2,
                        f"{Colors.DIM}The show goes on...{Colors.RESET}")
                time.sleep(1)
                sys.exit(0)
            elif choice in ['1', '2', '3', '4', '5', '6', '7']:
                execute_with_style(choice)
            else:
                print(f"\n{Colors.RED}Invalid input. Try again, Trader.{Colors.RESET}")
                time.sleep(1)
    finally:
        matrix_rain_active = False  # Ensure rain stops on exit

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Signal interrupted. Exiting...{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}System error: {str(e)}{Colors.RESET}")
        sys.exit(1)
