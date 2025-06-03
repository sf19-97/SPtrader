#!/usr/bin/env python3
"""
Execute QuestDB optimization queries to create viewport tables
"""

import requests
import time
import sys
import os

QUESTDB_URL = "http://localhost:9000/exec"

def execute_sql_file(filename):
    """Execute SQL statements from a file"""
    print(f"Reading SQL from {filename}...")
    
    with open(filename, 'r') as f:
        sql_content = f.read()
    
    # Split by semicolon but ignore semicolons inside parentheses
    statements = []
    current = []
    paren_count = 0
    
    for line in sql_content.split('\n'):
        # Skip comments and empty lines
        line = line.strip()
        if not line or line.startswith('--'):
            continue
            
        # Count parentheses to handle nested queries
        paren_count += line.count('(') - line.count(')')
        current.append(line)
        
        # If we hit a semicolon and we're not inside parentheses
        if line.endswith(';') and paren_count == 0:
            statements.append(' '.join(current))
            current = []
    
    # Execute each statement
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements):
        if not statement.strip():
            continue
            
        print(f"\nExecuting statement {i+1}/{len(statements)}:")
        print(f"  {statement[:80]}..." if len(statement) > 80 else f"  {statement}")
        
        try:
            response = requests.get(QUESTDB_URL, params={'query': statement})
            
            if response.status_code == 200:
                print(f"  ✓ Success")
                success_count += 1
                
                # Parse response for SELECT queries
                if statement.strip().upper().startswith('SELECT'):
                    try:
                        data = response.json()
                        if 'dataset' in data and data['dataset']:
                            print(f"  → Found {len(data['dataset'])} rows")
                    except:
                        pass
            else:
                print(f"  ✗ Error {response.status_code}: {response.text}")
                error_count += 1
                
        except requests.exceptions.ConnectionError:
            print("  ✗ Error: Cannot connect to QuestDB. Is it running on port 9000?")
            return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            error_count += 1
        
        # Small delay between queries
        time.sleep(0.1)
    
    print(f"\n{'='*60}")
    print(f"Execution complete:")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")
    print(f"{'='*60}")
    
    return error_count == 0

def check_questdb_connection():
    """Check if QuestDB is accessible"""
    try:
        response = requests.get("http://localhost:9000/")
        return response.status_code == 200
    except:
        return False

def main():
    print("QuestDB Optimization Script")
    print("="*60)
    
    # Check QuestDB connection
    if not check_questdb_connection():
        print("❌ Error: Cannot connect to QuestDB on http://localhost:9000")
        print("Please ensure QuestDB is running.")
        sys.exit(1)
    
    print("✓ Connected to QuestDB")
    
    # Execute optimization script
    # SQL file is now in the sql directory
    sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql", "optimize_questdb.sql")
    
    print(f"\nExecuting optimizations from {sql_file}...")
    success = execute_sql_file(sql_file)
    
    if success:
        print("\n✅ All optimizations completed successfully!")
        print("\nYour viewport tables are now ready. The API will automatically")
        print("select the best table based on the zoom level:")
        print("  - Year view: Daily aggregations")
        print("  - Month view: 4-hour aggregations")  
        print("  - Week view: 1-hour aggregations")
        print("  - Day view: Original fine-grained data")
    else:
        print("\n❌ Some optimizations failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()