# Electron Sandbox Mode

## Overview

The Chromium sandbox is a security feature that restricts what processes can do by limiting their access to system resources. In Electron, enabling the sandbox for renderer processes significantly improves security by preventing malicious code from accessing the file system, executing native modules, or using Node.js APIs directly.

## How Sandboxing Works

When a renderer process is sandboxed:

1. It has no Node.js environment (even if `nodeIntegration` is true)
2. It cannot access the file system directly
3. It cannot load native modules
4. It has limited access to system resources
5. It must communicate with the main process via IPC to perform privileged operations

## Enabling the Sandbox

### Global Sandboxing (Recommended)

Enable the sandbox for all renderer processes:

```javascript
// In main.js
app.enableSandbox()
```

### Per-Window Sandboxing

Enable the sandbox for specific BrowserWindow instances:

```javascript
// In main.js
const win = new BrowserWindow({
  webPreferences: {
    sandbox: true,
    contextIsolation: true,
    nodeIntegration: false
  }
})
```

## Working with Sandboxed Renderers

Since sandboxed renderers cannot access Node.js APIs directly, you must provide functionality through preload scripts and IPC:

### Preload Scripts with Sandbox

Even with sandbox enabled, preload scripts can use Node.js APIs to expose limited functionality:

```javascript
// In preload.js (with sandbox enabled)
const { contextBridge, ipcRenderer } = require('electron')

// Expose IPC communication to the renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // Provide access to file system via IPC
  readFile: (path) => ipcRenderer.invoke('read-file', path),
  writeFile: (path, data) => ipcRenderer.invoke('write-file', path, data),
  
  // Provide system information
  getAppPath: () => ipcRenderer.invoke('get-app-path')
})
```

### Main Process Handlers

In the main process, handle requests from the sandboxed renderer:

```javascript
// In main.js
const { ipcMain, app } = require('electron')
const fs = require('fs')

// Handle file reading requests
ipcMain.handle('read-file', async (event, path) => {
  // Security: Validate path is allowed
  if (!isPathAllowed(path)) {
    throw new Error('Access denied')
  }
  
  try {
    return await fs.promises.readFile(path, 'utf8')
  } catch (error) {
    throw new Error(`Failed to read file: ${error.message}`)
  }
})

// Determine if path is allowed (prevent path traversal)
function isPathAllowed(path) {
  const appDir = app.getAppPath()
  const userDataDir = app.getPath('userData')
  
  // Only allow files from specific directories
  return path.startsWith(appDir) || path.startsWith(userDataDir)
}
```

## Best Practices

### 1. Always Use Context Isolation with Sandbox

Combine sandbox with context isolation for maximum security:

```javascript
const win = new BrowserWindow({
  webPreferences: {
    sandbox: true,
    contextIsolation: true,
    nodeIntegration: false,
    preload: path.join(__dirname, 'preload.js')
  }
})
```

### 2. Sanitize and Validate All IPC Input

Since sandboxed renderers must use IPC for privileged operations, validate all input:

```javascript
// In main.js
ipcMain.handle('execute-query', async (event, query) => {
  // Validate query structure
  if (!query || typeof query !== 'object') {
    throw new Error('Invalid query format')
  }
  
  // Sanitize inputs to prevent SQL injection
  const sanitizedParams = sanitizeQueryParams(query.params)
  
  // Execute query with sanitized inputs
  return await database.execute(query.sql, sanitizedParams)
})
```

### 3. Create Separate Windows for Different Security Contexts

Use different BrowserWindow instances for different security needs:

```javascript
// Trusted content (internal pages)
const trustedWindow = new BrowserWindow({
  webPreferences: {
    sandbox: true,
    contextIsolation: true,
    preload: path.join(__dirname, 'trusted-preload.js')
  }
})
trustedWindow.loadFile('internal-dashboard.html')

// Untrusted content (external websites)
const untrustedWindow = new BrowserWindow({
  webPreferences: {
    sandbox: true,
    contextIsolation: true,
    nodeIntegration: false,
    // No preload script for untrusted content
  }
})
untrustedWindow.loadURL('https://example.com')
```

### 4. Set Appropriate Permissions

Restrict permissions for sandboxed renderers:

```javascript
// In main.js
win.webContents.session.setPermissionRequestHandler(
  (webContents, permission, callback) => {
    // Allow only specific permissions
    const allowedPermissions = ['clipboard-read', 'clipboard-write']
    callback(allowedPermissions.includes(permission))
  }
)
```

## Troubleshooting Sandbox Issues

### Common Errors

#### 1. Cannot Access Node.js Modules

**Problem:** Code in a sandboxed renderer tries to use Node.js modules directly.

**Solution:** Move the Node.js code to the main process and expose functionality via IPC.

```javascript
// WRONG (in renderer):
const fs = require('fs') // This will fail in sandboxed renderer

// CORRECT (in preload):
contextBridge.exposeInMainWorld('electronAPI', {
  readFile: (path) => ipcRenderer.invoke('read-file', path)
})

// CORRECT (in main):
ipcMain.handle('read-file', async (event, path) => {
  // Use fs module here
})
```

#### 2. Native Modules Not Working

**Problem:** Native modules cannot be loaded in sandboxed renderers.

**Solution:** Access native functionality from the main process.

```javascript
// In main.js
const native = require('some-native-module')

ipcMain.handle('native-operation', async (event, ...args) => {
  return native.performOperation(...args)
})

// In preload.js
contextBridge.exposeInMainWorld('electronAPI', {
  performNativeOperation: (...args) => ipcRenderer.invoke('native-operation', ...args)
})
```

#### 3. Cannot Access Local Resources

**Problem:** Sandboxed renderers cannot access local files directly.

**Solution:** Use proper protocols or serve content through the main process.

```javascript
// In main.js
protocol.registerFileProtocol('app', (request, callback) => {
  const url = request.url.substr(6) // Remove 'app://'
  callback({ path: path.join(__dirname, 'resources', url) })
})

// In renderer
// Use app:// protocol
document.getElementById('image').src = 'app://images/logo.png'
```

## Sandbox Compatibility

### Testing Sandbox Compatibility

To verify your app works with sandbox enabled:

1. Enable sandbox globally with `app.enableSandbox()`
2. Run your application and test all functionality
3. Check for errors in the console related to Node.js access or native modules
4. Move any incompatible code to the main process and expose via IPC

### Migrating to Sandbox Mode

If your app currently runs without sandbox:

1. Enable sandbox for one window at a time
2. Identify functionality that breaks
3. Refactor code to use IPC for privileged operations
4. Update preload scripts to use contextBridge
5. Verify functionality after each change
6. Finally enable sandbox globally