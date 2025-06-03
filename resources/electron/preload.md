# Electron Preload Scripts and Context Isolation

## Overview

Preload scripts are loaded before the renderer process starts. They have access to both Node.js APIs and the DOM, making them ideal for securely exposing main process functionality to the renderer process through the contextBridge.

## Context Isolation

Context isolation is a security feature that ensures the preload script and renderer process run in separate JavaScript contexts. This prevents attackers from accessing Node.js APIs even if they manage to execute arbitrary code in the renderer process.

## Key Concepts

### 1. Setting Up a Preload Script

```javascript
// In main.js
const mainWindow = new BrowserWindow({
  width: 800,
  height: 600,
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,  // Enable context isolation
    nodeIntegration: false,  // Disable direct Node.js access
    sandbox: true            // Enable Chromium sandbox
  }
})
```

### 2. Using contextBridge

```javascript
// In preload.js
const { contextBridge, ipcRenderer } = require('electron')

// Expose validated APIs to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Synchronous getter
  platform: process.platform,
  
  // Async messaging - send
  sendMessage: (message) => ipcRenderer.send('message', message),
  
  // Async messaging - request/response
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Async messaging - receive
  onUpdateAvailable: (callback) => {
    ipcRenderer.on('update-available', callback)
    return () => ipcRenderer.removeListener('update-available', callback)
  }
})
```

### 3. Accessing Exposed APIs in Renderer

```javascript
// In renderer.js
console.log(`Running on ${window.electronAPI.platform}`)

// Send message to main process
document.getElementById('sendButton').addEventListener('click', () => {
  window.electronAPI.sendMessage('Hello from button click')
})

// Request data from main process
async function getVersion() {
  try {
    const version = await window.electronAPI.getAppVersion()
    document.getElementById('version').textContent = version
  } catch (error) {
    console.error('Error getting version:', error)
  }
}

// Listen for events from main process
const removeListener = window.electronAPI.onUpdateAvailable((event, info) => {
  console.log(`Update available: ${info.version}`)
  // When done listening
  // removeListener()
})
```

## Security Best Practices

### 1. Validate All Input Parameters

```javascript
// In preload.js
contextBridge.exposeInMainWorld('electronAPI', {
  saveFile: (content, filePath) => {
    // Validate parameters
    if (typeof content !== 'string') {
      throw new Error('Content must be a string')
    }
    
    if (typeof filePath !== 'string' || !filePath.endsWith('.txt')) {
      throw new Error('Invalid file path. Only .txt files are allowed.')
    }
    
    // Proceed with save operation
    return ipcRenderer.invoke('save-file', { content, filePath })
  }
})
```

### 2. Use Function Overloading Instead of Direct IPC Access

```javascript
// BAD - Exposing IPC directly
contextBridge.exposeInMainWorld('electron', {
  ipcRenderer: ipcRenderer // NEVER DO THIS
})

// GOOD - Exposing specific functionality
contextBridge.exposeInMainWorld('electronAPI', {
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (content) => ipcRenderer.invoke('dialog:saveFile', content)
})
```

### 3. Limit Access to Return Values

```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  // Only return specific properties to avoid leaking sensitive information
  getSystemInfo: async () => {
    const info = await ipcRenderer.invoke('get-system-info')
    return {
      platform: info.platform,
      arch: info.arch,
      version: info.version
      // Omit sensitive properties like MAC addresses, usernames, etc.
    }
  }
})
```

### 4. Use Typed APIs

```javascript
// In preload.js with TypeScript or JSDoc
/**
 * @typedef {Object} FileFilter
 * @property {string} name - Display name for the filter
 * @property {string[]} extensions - Allowed file extensions
 */

/**
 * Opens a file dialog and returns selected file paths
 * @param {Object} options
 * @param {string} options.title - Dialog title
 * @param {FileFilter[]} options.filters - File filters
 * @param {boolean} options.multiSelections - Allow multiple selections
 * @returns {Promise<string[]>} Selected file paths
 */
const openFileDialog = (options) => {
  // Validate options
  if (typeof options !== 'object') {
    throw new Error('Options must be an object')
  }
  
  return ipcRenderer.invoke('dialog:openFile', options)
}

contextBridge.exposeInMainWorld('electronAPI', {
  openFileDialog
})
```

## Common Patterns

### 1. Two-way Communication with Callbacks

```javascript
// In preload.js
contextBridge.exposeInMainWorld('electronAPI', {
  performLongTask: (taskData, progressCallback) => {
    // Generate a unique channel for this specific task
    const progressChannel = `progress-${Date.now()}`
    
    // Set up temporary listener for progress
    const progressListener = (event, progress) => {
      progressCallback(progress)
    }
    
    ipcRenderer.on(progressChannel, progressListener)
    
    // Call main process with the unique channel
    return ipcRenderer.invoke('long-task', { taskData, progressChannel })
      .finally(() => {
        // Clean up listener when task is complete
        ipcRenderer.removeListener(progressChannel, progressListener)
      })
  }
})
```

### 2. Module-based Organization

```javascript
// In preload.js
const { contextBridge, ipcRenderer } = require('electron')

// File operations API
const fileAPI = {
  open: () => ipcRenderer.invoke('file:open'),
  save: (content) => ipcRenderer.invoke('file:save', content),
  export: (format) => ipcRenderer.invoke('file:export', format)
}

// Application API
const appAPI = {
  getVersion: () => ipcRenderer.invoke('app:version'),
  checkForUpdates: () => ipcRenderer.invoke('app:check-updates'),
  quit: () => ipcRenderer.send('app:quit')
}

// Expose APIs to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  file: fileAPI,
  app: appAPI
})
```

### 3. Event Subscriptions

```javascript
// In preload.js
const validChannels = ['update-available', 'download-progress', 'log-message']

contextBridge.exposeInMainWorld('electronAPI', {
  // Subscribe to events
  on: (channel, callback) => {
    if (validChannels.includes(channel)) {
      const subscription = (event, ...args) => callback(...args)
      ipcRenderer.on(channel, subscription)
      
      // Return unsubscribe function
      return () => {
        ipcRenderer.removeListener(channel, subscription)
      }
    }
    return null
  }
})

// In renderer.js
const unsubscribe = window.electronAPI.on('download-progress', (progress) => {
  updateProgressBar(progress)
})

// When no longer needed
unsubscribe()
```

## Best Practices

1. **Keep preload scripts minimal** - They should only expose necessary APIs
2. **Avoid DOM manipulation in preload** - Focus on exposing APIs, not UI changes
3. **Validate all inputs and outputs** - Never trust data crossing process boundaries
4. **Don't expose entire modules** - Only expose specific functionality
5. **Use specific channel names** - Avoid generic names like 'message' or 'data'
6. **Clean up listeners** - Provide ways to remove listeners when no longer needed
7. **Add error handling** - Catch and report errors from IPC operations
8. **Update with Electron** - contextBridge API may change between versions