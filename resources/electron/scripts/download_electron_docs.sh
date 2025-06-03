#!/bin/bash
# download_electron_docs.sh
# Downloads Electron documentation for offline searching

# Set the target directory
DOCS_DIR="/home/millet_frazier/SPtrader/resources/electron/official_docs"
mkdir -p "$DOCS_DIR"
cd "$DOCS_DIR"

# Clear existing files if needed
# rm -f *.html

# Download key documentation pages
echo "Downloading Electron documentation..."

# Main pages
wget -q -O index.html https://www.electronjs.org/docs/latest/
echo "Downloaded main index"

# Core concepts
wget -q -O process_model.html https://www.electronjs.org/docs/latest/tutorial/process-model
wget -q -O quick_start.html https://www.electronjs.org/docs/latest/tutorial/quick-start
wget -q -O architecture.html https://www.electronjs.org/docs/latest/tutorial/architecture
echo "Downloaded core concepts"

# Main process
wget -q -O main_process.html https://www.electronjs.org/docs/latest/tutorial/main-process
wget -q -O window_management.html https://www.electronjs.org/docs/latest/tutorial/window-customization
wget -q -O notification.html https://www.electronjs.org/docs/latest/tutorial/notifications
echo "Downloaded main process guides"

# Renderer process
wget -q -O web_contents.html https://www.electronjs.org/docs/latest/api/web-contents
wget -q -O browser_window.html https://www.electronjs.org/docs/latest/api/browser-window
wget -q -O webview_tag.html https://www.electronjs.org/docs/latest/api/webview-tag
echo "Downloaded renderer process guides"

# IPC communication
wget -q -O ipc_main.html https://www.electronjs.org/docs/latest/api/ipc-main
wget -q -O ipc_renderer.html https://www.electronjs.org/docs/latest/api/ipc-renderer
wget -q -O context_bridge.html https://www.electronjs.org/docs/latest/api/context-bridge
echo "Downloaded IPC communication guides"

# Security
wget -q -O security.html https://www.electronjs.org/docs/latest/tutorial/security
wget -q -O sandbox.html https://www.electronjs.org/docs/latest/tutorial/sandbox
wget -q -O context_isolation.html https://www.electronjs.org/docs/latest/tutorial/context-isolation
echo "Downloaded security guides"

# Native features
wget -q -O clipboard.html https://www.electronjs.org/docs/latest/api/clipboard
wget -q -O dialog.html https://www.electronjs.org/docs/latest/api/dialog
wget -q -O menu.html https://www.electronjs.org/docs/latest/api/menu
wget -q -O shell.html https://www.electronjs.org/docs/latest/api/shell
echo "Downloaded native features guides"

# Web technologies
wget -q -O offscreen_rendering.html https://www.electronjs.org/docs/latest/tutorial/offscreen-rendering
wget -q -O web_workers.html https://www.electronjs.org/docs/latest/tutorial/web-workers
wget -q -O devtools_extension.html https://www.electronjs.org/docs/latest/tutorial/devtools-extension
echo "Downloaded web technologies guides"

# Testing and debugging
wget -q -O debugging.html https://www.electronjs.org/docs/latest/tutorial/debugging-main-process
wget -q -O testing.html https://www.electronjs.org/docs/latest/tutorial/automated-testing
wget -q -O application_debugging.html https://www.electronjs.org/docs/latest/tutorial/application-debugging
echo "Downloaded testing and debugging guides"

echo "Documentation download complete!"
echo "Files saved to: $DOCS_DIR"