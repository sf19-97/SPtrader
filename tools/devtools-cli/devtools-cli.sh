#!/bin/bash
# DevTools CLI for SPtrader

# Default output to JSON
OUTPUT_FORMAT=${2:-json}

# Change to the CLI directory
cd /home/millet_frazier/SPtrader/tools/devtools-cli

# Execute the command
case "$1" in
  "network")
    node devtools.js network
    ;;
  "elements")
    node devtools.js elements "$2"
    ;;
  "console")
    node devtools.js console
    ;;
  "performance")
    node devtools.js performance
    ;;
  "state")
    node devtools.js state
    ;;
  *)
    node devtools.js help
    ;;
esac

# If output format is requested as text and a JSON file exists, convert it
if [[ "$OUTPUT_FORMAT" == "text" ]]; then
  OUTPUT_FILE="output/$(echo $1).json"
  if [[ -f "$OUTPUT_FILE" ]]; then
    cat "$OUTPUT_FILE" | json_pp
  fi
fi