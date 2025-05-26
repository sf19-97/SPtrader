#!/bin/bash
#
# manage_logs.sh - SPtrader Log Management System
#
# Description:
#   Provides comprehensive log management functionality including cleaning,
#   rotating, and analyzing logs. Maintains separation between runtime logs
#   (continuous service output) and status logs (latest test results).
#
# Log Structure:
#   logs/runtime/  - Continuous service logs that append over time
#   logs/status/   - Status snapshots that overwrite each run
#   logs/archive/  - Compressed historical logs
#
# Commands:
#   show    - Display log sizes, ages, and locations
#   clean   - Delete logs (with options for selective deletion)
#   rotate  - Archive and compress old logs
#   tail    - Follow specific logs in real-time
#
# Usage:
#   ./manage_logs.sh show              # Show all log info
#   ./manage_logs.sh clean all         # Delete all logs
#   ./manage_logs.sh clean runtime     # Delete only runtime logs
#   ./manage_logs.sh clean status      # Delete only status logs
#   ./manage_logs.sh rotate            # Archive logs older than 24h
#   ./manage_logs.sh tail oanda_feed   # Follow specific log

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Paths
LOG_BASE="$HOME/SPtrader/logs"
RUNTIME_DIR="$LOG_BASE/runtime"
STATUS_DIR="$LOG_BASE/status"
ARCHIVE_DIR="$LOG_BASE/archive"

# Ensure directories exist
mkdir -p "$RUNTIME_DIR" "$STATUS_DIR" "$ARCHIVE_DIR"

# Function to format file size
format_size() {
    local size=$1
    if [ $size -lt 1024 ]; then
        echo "${size}B"
    elif [ $size -lt 1048576 ]; then
        echo "$((size/1024))KB"
    elif [ $size -lt 1073741824 ]; then
        echo "$((size/1048576))MB"
    else
        echo "$((size/1073741824))GB"
    fi
}

# Function to get file age in human-readable format
get_file_age() {
    local file=$1
    if [ -f "$file" ]; then
        local now=$(date +%s)
        local file_time=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
        local age=$((now - file_time))
        
        if [ $age -lt 3600 ]; then
            echo "$((age/60))m ago"
        elif [ $age -lt 86400 ]; then
            echo "$((age/3600))h ago"
        else
            echo "$((age/86400))d ago"
        fi
    else
        echo "N/A"
    fi
}

# Show log information
show_logs() {
    echo -e "${BLUE}=== SPtrader Log Status ===${NC}"
    echo ""
    
    # Runtime logs
    echo -e "${CYAN}Runtime Logs (continuous):${NC}"
    echo -e "${YELLOW}Location: $RUNTIME_DIR${NC}"
    printf "%-25s %-10s %-15s %s\n" "Log File" "Size" "Last Modified" "Status"
    printf "%-25s %-10s %-15s %s\n" "--------" "----" "-------------" "------"
    
    for log in oanda_feed.log ohlc_manager.log fastapi.log questdb.log frontend.log; do
        if [ -f "$RUNTIME_DIR/$log" ]; then
            size=$(stat -c%s "$RUNTIME_DIR/$log" 2>/dev/null || stat -f%z "$RUNTIME_DIR/$log" 2>/dev/null || echo 0)
            age=$(get_file_age "$RUNTIME_DIR/$log")
            formatted_size=$(format_size $size)
            
            # Color code by size
            if [ $size -gt 104857600 ]; then  # > 100MB
                status="${RED}Large${NC}"
            elif [ $size -gt 10485760 ]; then  # > 10MB
                status="${YELLOW}Growing${NC}"
            else
                status="${GREEN}OK${NC}"
            fi
            
            printf "%-25s %-10s %-15s %b\n" "$log" "$formatted_size" "$age" "$status"
        else
            printf "%-25s %-10s %-15s %s\n" "$log" "-" "-" "Not found"
        fi
    done
    
    # Status logs
    echo ""
    echo -e "${CYAN}Status Logs (overwritten):${NC}"
    echo -e "${YELLOW}Location: $STATUS_DIR${NC}"
    printf "%-25s %-10s %-15s\n" "Log File" "Size" "Last Updated"
    printf "%-25s %-10s %-15s\n" "--------" "----" "------------"
    
    for log in connectivity_test.log startup_summary.log last_error.log; do
        if [ -f "$STATUS_DIR/$log" ]; then
            size=$(stat -c%s "$STATUS_DIR/$log" 2>/dev/null || stat -f%z "$STATUS_DIR/$log" 2>/dev/null || echo 0)
            age=$(get_file_age "$STATUS_DIR/$log")
            formatted_size=$(format_size $size)
            printf "%-25s %-10s %-15s\n" "$log" "$formatted_size" "$age"
        else
            printf "%-25s %-10s %-15s\n" "$log" "-" "Not found"
        fi
    done
    
    # Archive info
    echo ""
    echo -e "${CYAN}Archive Status:${NC}"
    echo -e "${YELLOW}Location: $ARCHIVE_DIR${NC}"
    archive_count=$(ls -1 "$ARCHIVE_DIR"/*.tar.gz 2>/dev/null | wc -l)
    if [ $archive_count -gt 0 ]; then
        archive_size=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
        echo "  Archives: $archive_count files, Total size: $archive_size"
        
        # Show latest archives
        echo "  Recent archives:"
        ls -1t "$ARCHIVE_DIR"/*.tar.gz 2>/dev/null | head -3 | while read archive; do
            basename=$(basename "$archive")
            size=$(stat -c%s "$archive" 2>/dev/null || stat -f%z "$archive" 2>/dev/null || echo 0)
            formatted_size=$(format_size $size)
            echo "    - $basename ($formatted_size)"
        done
    else
        echo "  No archives found"
    fi
    
    # Total disk usage
    echo ""
    total_size=$(du -sh "$LOG_BASE" 2>/dev/null | cut -f1)
    echo -e "${BLUE}Total log disk usage: $total_size${NC}"
}

# Clean logs
clean_logs() {
    local target=$1
    
    case "$target" in
        all)
            echo -e "${YELLOW}Cleaning all logs...${NC}"
            read -p "Are you sure you want to delete ALL logs? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f "$RUNTIME_DIR"/*.log
                rm -f "$STATUS_DIR"/*.log
                rm -f "$ARCHIVE_DIR"/*.tar.gz
                echo -e "${GREEN}✓ All logs cleaned${NC}"
            else
                echo "Cancelled"
            fi
            ;;
        runtime)
            echo -e "${YELLOW}Cleaning runtime logs...${NC}"
            rm -f "$RUNTIME_DIR"/*.log
            echo -e "${GREEN}✓ Runtime logs cleaned${NC}"
            ;;
        status)
            echo -e "${YELLOW}Cleaning status logs...${NC}"
            rm -f "$STATUS_DIR"/*.log
            echo -e "${GREEN}✓ Status logs cleaned${NC}"
            ;;
        archive)
            echo -e "${YELLOW}Cleaning archive logs...${NC}"
            read -p "Delete all archived logs? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f "$ARCHIVE_DIR"/*.tar.gz
                echo -e "${GREEN}✓ Archives cleaned${NC}"
            else
                echo "Cancelled"
            fi
            ;;
        *)
            echo -e "${RED}Usage: $0 clean [all|runtime|status|archive]${NC}"
            exit 1
            ;;
    esac
}

# Rotate logs
rotate_logs() {
    echo -e "${BLUE}=== Rotating Logs ===${NC}"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local archive_name="runtime_logs_$timestamp.tar.gz"
    local rotated_count=0
    
    # Create temporary directory for logs to rotate
    local temp_dir=$(mktemp -d)
    
    # Check each runtime log
    for log in "$RUNTIME_DIR"/*.log; do
        if [ -f "$log" ]; then
            basename=$(basename "$log")
            size=$(stat -c%s "$log" 2>/dev/null || stat -f%z "$log" 2>/dev/null || echo 0)
            
            # Rotate if > 10MB or older than 24 hours
            if [ $size -gt 10485760 ] || [ $(find "$log" -mtime +1 2>/dev/null | wc -l) -gt 0 ]; then
                echo -e "${YELLOW}Rotating $basename ($(format_size $size))...${NC}"
                cp "$log" "$temp_dir/"
                echo "" > "$log"  # Clear the original
                ((rotated_count++))
            fi
        fi
    done
    
    # Create archive if any logs were rotated
    if [ $rotated_count -gt 0 ]; then
        echo -e "${YELLOW}Creating archive...${NC}"
        tar -czf "$ARCHIVE_DIR/$archive_name" -C "$temp_dir" .
        echo -e "${GREEN}✓ Archived $rotated_count logs to $archive_name${NC}"
        
        # Clean up old archives (keep last 7)
        echo -e "${YELLOW}Cleaning old archives...${NC}"
        ls -1t "$ARCHIVE_DIR"/*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -f
        echo -e "${GREEN}✓ Kept last 7 archives${NC}"
    else
        echo -e "${GREEN}No logs need rotation${NC}"
    fi
    
    # Clean up
    rm -rf "$temp_dir"
}

# Tail specific log
tail_log() {
    local log_name=$1
    
    # Try runtime directory first
    if [ -f "$RUNTIME_DIR/$log_name.log" ]; then
        echo -e "${CYAN}Following $RUNTIME_DIR/$log_name.log${NC}"
        echo "Press Ctrl+C to stop"
        tail -f "$RUNTIME_DIR/$log_name.log"
    elif [ -f "$STATUS_DIR/$log_name.log" ]; then
        echo -e "${CYAN}Following $STATUS_DIR/$log_name.log${NC}"
        echo "Press Ctrl+C to stop"
        tail -f "$STATUS_DIR/$log_name.log"
    else
        echo -e "${RED}Log not found: $log_name.log${NC}"
        echo "Available logs:"
        ls -1 "$RUNTIME_DIR"/*.log "$STATUS_DIR"/*.log 2>/dev/null | xargs -n1 basename | sed 's/\.log$//'
        exit 1
    fi
}

# Main command processing
case "$1" in
    show|"")
        show_logs
        ;;
    clean)
        clean_logs "${2:-all}"
        ;;
    rotate)
        rotate_logs
        ;;
    tail)
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: $0 tail <log_name>${NC}"
            echo "Example: $0 tail oanda_feed"
            exit 1
        fi
        tail_log "$2"
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Usage: $0 [show|clean|rotate|tail]"
        exit 1
        ;;
esac