#!/bin/bash
# download_questdb_docs.sh
# Downloads QuestDB documentation for offline searching

# Set the target directory
DOCS_DIR="/home/millet_frazier/SPtrader/resources/questdb/official_docs"
mkdir -p "$DOCS_DIR"
cd "$DOCS_DIR"

# Clear existing files if needed
# rm -f *.html

# Download key documentation pages
echo "Downloading QuestDB documentation..."

# Main SQL reference
wget -q -O sql_reference.html https://questdb.io/docs/reference/sql/
echo "Downloaded SQL reference"

# Key SQL features
wget -q -O sql_extensions.html https://questdb.io/docs/concept/sql-extensions/
echo "Downloaded SQL extensions"

# Important SQL commands
wget -q -O select.html https://questdb.io/docs/reference/sql/select/
wget -q -O where.html https://questdb.io/docs/reference/sql/where/
wget -q -O sample_by.html https://questdb.io/docs/reference/sql/sample-by/
wget -q -O join.html https://questdb.io/docs/reference/sql/join/
wget -q -O latest_by.html https://questdb.io/docs/reference/sql/latest-by/
wget -q -O timestamp.html https://questdb.io/docs/reference/sql/timestamp/
echo "Downloaded SQL commands reference"

# Data types
wget -q -O datatypes.html https://questdb.io/docs/reference/sql/datatypes/
echo "Downloaded data types reference"

# Functions
wget -q -O functions.html https://questdb.io/docs/reference/function/
echo "Downloaded functions reference"

# Table operations
wget -q -O create_table.html https://questdb.io/docs/reference/sql/create-table/
wget -q -O alter_table.html https://questdb.io/docs/reference/sql/alter-table/
wget -q -O drop_table.html https://questdb.io/docs/reference/sql/drop-table/
echo "Downloaded table operations reference"

# Best practices
wget -q -O partitioning.html https://questdb.io/docs/concept/partitioning/
wget -q -O designated_timestamp.html https://questdb.io/docs/concept/designated-timestamp/
echo "Downloaded best practices guides"

echo "Documentation download complete!"
echo "Files saved to: $DOCS_DIR"