#!/bin/bash
# search_docs.sh
# Search Electron documentation for specific topics

# Check if search term is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <search_term>"
    echo "Example: $0 \"sandbox\""
    exit 1
fi

SEARCH_TERM="$1"
DOCS_DIR="/home/millet_frazier/SPtrader/resources/electron"

echo "Searching for: $SEARCH_TERM"
echo "=========================="

# Search in markdown files
echo -e "\n📑 Documentation Files:"
echo "----------------------"
grep -r -i -n --color=always "$SEARCH_TERM" "$DOCS_DIR" --include="*.md" | while read -r line; do
    echo "$line"
    echo "-----------------------------------------"
done

# Search in JS examples
echo -e "\n📊 JavaScript Examples:"
echo "--------------------"
grep -r -i -n --color=always "$SEARCH_TERM" "$DOCS_DIR/examples" --include="*.js" || echo "No matches in JavaScript examples"

# Search in official docs HTML files
echo -e "\n📚 Official Documentation:"
echo "------------------------"
grep -r -i -n --color=always "$SEARCH_TERM" "$DOCS_DIR/official_docs" --include="*.html" | grep -v "<script\|<style\|<meta" | head -n 20 || echo "No matches in official documentation"

# Search in troubleshooting
echo -e "\n🔧 Troubleshooting:"
echo "----------------"
grep -r -i -n --color=always "$SEARCH_TERM" "$DOCS_DIR/troubleshooting" || echo "No matches in troubleshooting guides"

# Search in security guides
echo -e "\n🔒 Security Guidelines:"
echo "-------------------"
grep -r -i -n --color=always "$SEARCH_TERM" "$DOCS_DIR/security" || echo "No matches in security guidelines"

# Search in IPC documentation
echo -e "\n🔄 IPC Communication:"
echo "-----------------"
grep -r -i -n --color=always "$SEARCH_TERM" "$DOCS_DIR/ipc" || echo "No matches in IPC documentation"

echo -e "\nSearch complete."
echo "For more specific results, try narrowing your search term."
echo "Example: ./search_docs.sh \"contextBridge\""