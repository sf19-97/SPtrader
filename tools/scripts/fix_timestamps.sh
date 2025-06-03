#\!/bin/bash
# Fix timestamps on all OHLC generator scripts
# Created: May 31, 2025

# Update timestamp on simple_ohlc_generator.py
touch -d "May 31, 2025 22:30:00" simple_ohlc_generator.py

# Mark old script as deprecated
touch -d "May 31, 2025 22:30:00" build_all_timeframes.py.deprecated

# Create symlink to the new script for backward compatibility
ln -sf simple_ohlc_generator.py build_all_timeframes.py
touch -d "May 31, 2025 22:30:00" build_all_timeframes.py

echo "✅ OHLC generator scripts updated"
