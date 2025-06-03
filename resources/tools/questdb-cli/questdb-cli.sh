#!/bin/bash
# QuestDB CLI - Command-line interface for QuestDB
# Created: May 31, 2025

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set NODE_ENV if not already set
if [ -z "$NODE_ENV" ]; then
  export NODE_ENV="development"
fi

# Execute the command
cd "$SCRIPT_DIR"
node questdb-cli.js "$@"