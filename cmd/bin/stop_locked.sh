#!/bin/bash
echo "Stopping locked services..."
if [ -f /tmp/sptrader_api.pid ]; then
    kill $(cat /tmp/sptrader_api.pid) 2>/dev/null
    rm /tmp/sptrader_api.pid
fi
pkill -f questdb
echo "Done"
