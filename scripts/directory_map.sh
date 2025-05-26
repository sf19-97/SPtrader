#!/bin/bash
cd "$(dirname "$0")"
tree -a -I '.git|node_modules' > directory_map.txt
xdg-open directory_map.txt
