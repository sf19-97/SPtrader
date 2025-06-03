# Electron IPC Communication Patterns

## Overview

Inter-Process Communication (IPC) in Electron allows the main process and renderer processes to communicate with each other. This guide covers common patterns and best practices for IPC in Electron applications.

## IPC Modules

Electron provides two core modules for IPC:

- `ipcMain`: Used in the main process to handle communication from renderers
- `ipcRenderer`: Used in renderer processes to communicate with the main process

With context isolation enabled (recommended), renderer processes access IPC through the exposed API in the preload script.

## Communication Patterns

### 1. One-Way Communication (Fire and Forget)

#### Main Process (Receiver)

```javascript
// In main.js
const { ipcMain } = require('electron')

// Listen for messages from renderer
ipcMain.on('log-message', (event, message) => {
  console.log('Message from renderer:', message)
  // No response sent back
})
```

#### Preload Script

```javascript
// In preload.js
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  logMessage: (message) => ipcRenderer.send('log-message', message)
})
```

#### Renderer Process

```javascript
// In renderer.js
document.getElementById('logButton').addEventListener('click', () => {
  window.electronAPI.logMessage('Button clicked at ' + new Date())
})
```

### 2. Request-Response Pattern (Async)

#### Main Process (Responder)

```javascript
// In main.js
const { ipcMain } = require('electron')

// Handle requests from renderer
ipcMain.handle('get-app-info', async (event, args) => {
  // Perform operations, can be async
  const appInfo = {
    name: app.getName(),
    version: app.getVersion(),
    platform: process.platform,
    // Only include requested fields if specified
    ...(args?.fields === 'extended' && {
      locale: app.getLocale(),
      paths: {
        userData: app.getPath('userData'),
        logs: app.getPath('logs')
      }
    })
  }
  
  return appInfo
})
```

#### Preload Script

```javascript
// In preload.js
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  getAppInfo: (args) => ipcRenderer.invoke('get-app-info', args)
})
```

#### Renderer Process

```javascript
// In renderer.js
async function displayAppInfo() {
  try {
    // Basic info
    const basicInfo = await window.electronAPI.getAppInfo()
    console.log('App info:', basicInfo)
    
    // Extended info
    const extendedInfo = await window.electronAPI.getAppInfo({ fields: 'extended' })
    console.log('Extended info:', extendedInfo)
  } catch (error) {
    console.error('Failed to get app info:', error)
  }
}
```

### 3. Publish-Subscribe Pattern (Events)

#### Main Process (Publisher)

```javascript
// In main.js
let mainWindow

// Send updates to renderer
function sendStatusUpdate(status) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('status-update', status)
  }
}

// Example: periodic updates
setInterval(() => {
  const status = {
    cpuUsage: process.getCPUUsage(),
    memoryUsage: process.getSystemMemoryInfo(),
    timestamp: Date.now()
  }
  sendStatusUpdate(status)
}, 5000)
```

#### Preload Script

```javascript
// In preload.js
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  onStatusUpdate: (callback) => {
    const statusListener = (event, status) => {
      callback(status)
    }
    
    // Add listener
    ipcRenderer.on('status-update', statusListener)
    
    // Return function to remove listener
    return () => {
      ipcRenderer.removeListener('status-update', statusListener)
    }
  }
})
```

#### Renderer Process

```javascript
// In renderer.js
// Set up subscription
const unsubscribe = window.electronAPI.onStatusUpdate((status) => {
  document.getElementById('cpu-usage').textContent = `${status.cpuUsage.percentCPUUsage.toFixed(2)}%`
  document.getElementById('memory-usage').textContent = `${Math.round(status.memoryUsage.free / 1024 / 1024)}MB free`
  document.getElementById('last-update').textContent = new Date(status.timestamp).toLocaleTimeString()
})

// Clean up when component unmounts or page changes
function cleanup() {
  if (unsubscribe) {
    unsubscribe()
  }
}
```

### 4. Progress Reporting Pattern

#### Main Process

```javascript
// In main.js
const { ipcMain } = require('electron')
const fs = require('fs')

ipcMain.handle('process-large-file', async (event, { filePath, progressChannel }) => {
  try {
    const stats = fs.statSync(filePath)
    const fileSize = stats.size
    const chunkSize = 1024 * 1024 // 1MB chunks
    let processedBytes = 0
    
    return new Promise((resolve, reject) => {
      // Create read stream
      const stream = fs.createReadStream(filePath, { highWaterMark: chunkSize })
      
      stream.on('data', (chunk) => {
        // Process chunk...
        processedBytes += chunk.length
        
        // Report progress
        const progress = Math.min(100, Math.round((processedBytes / fileSize) * 100))
        event.sender.send(progressChannel, { progress, processedBytes, fileSize })
      })
      
      stream.on('end', () => {
        resolve({ success: true, processedBytes, fileSize })
      })
      
      stream.on('error', (error) => {
        reject(error)
      })
    })
  } catch (error) {
    console.error('Error processing file:', error)
    throw error
  }
})
```

#### Preload Script

```javascript
// In preload.js
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  processLargeFile: (filePath, progressCallback) => {
    // Create unique channel for this operation
    const progressChannel = `file-progress-${Date.now()}`
    
    // Set up progress listener
    const progressListener = (event, progress) => {
      progressCallback(progress)
    }
    
    ipcRenderer.on(progressChannel, progressListener)
    
    // Invoke main process function
    return ipcRenderer.invoke('process-large-file', { 
      filePath, 
      progressChannel 
    }).finally(() => {
      // Clean up listener when done
      ipcRenderer.removeListener(progressChannel, progressListener)
    })
  }
})
```

#### Renderer Process

```javascript
// In renderer.js
const progressBar = document.getElementById('progress-bar')
const statusText = document.getElementById('status-text')

document.getElementById('process-button').addEventListener('click', async () => {
  try {
    const filePath = document.getElementById('file-path').value
    
    progressBar.value = 0
    statusText.textContent = 'Starting...'
    
    // Process file with progress reporting
    const result = await window.electronAPI.processLargeFile(
      filePath,
      (progress) => {
        // Update UI with progress
        progressBar.value = progress.progress
        statusText.textContent = `Processing: ${progress.progress}% (${formatBytes(progress.processedBytes)} of ${formatBytes(progress.fileSize)})`
      }
    )
    
    statusText.textContent = `Complete! Processed ${formatBytes(result.processedBytes)}`
  } catch (error) {
    statusText.textContent = `Error: ${error.message}`
  }
})

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B'
  else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB'
  else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB'
  else return (bytes / 1073741824).toFixed(2) + ' GB'
}
```

## Best Practices

### 1. Use Typed Channels

Create a central file to define IPC channel names:

```javascript
// In ipc-channels.js
module.exports = {
  APP: {
    GET_INFO: 'app:get-info',
    QUIT: 'app:quit',
    UPDATE_AVAILABLE: 'app:update-available'
  },
  FILE: {
    OPEN: 'file:open',
    SAVE: 'file:save',
    PROCESS: 'file:process',
    PROGRESS: 'file:progress'
  },
  SYSTEM: {
    STATUS_UPDATE: 'system:status-update',
    ERROR: 'system:error'
  }
}
```

Then use these in both main and preload scripts:

```javascript
// In main.js
const IPC_CHANNELS = require('./ipc-channels')

ipcMain.handle(IPC_CHANNELS.APP.GET_INFO, () => {
  return { /* app info */ }
})

// In preload.js
const IPC_CHANNELS = require('./ipc-channels')

contextBridge.exposeInMainWorld('electronAPI', {
  getAppInfo: () => ipcRenderer.invoke(IPC_CHANNELS.APP.GET_INFO)
})
```

### 2. Validate All Input

```javascript
// In main.js
ipcMain.handle('save-file', async (event, { content, filePath }) => {
  // Validate input parameters
  if (typeof content !== 'string') {
    throw new Error('Content must be a string')
  }
  
  if (typeof filePath !== 'string') {
    throw new Error('File path must be a string')
  }
  
  // Validate file path for security
  const normalizedPath = path.normalize(filePath)
  const userDataDir = app.getPath('userData')
  
  if (!normalizedPath.startsWith(userDataDir)) {
    throw new Error('Cannot write outside user data directory')
  }
  
  // Proceed with operation if validation passes
  await fs.promises.writeFile(normalizedPath, content)
  return { success: true, path: normalizedPath }
})
```

### 3. Handle Errors Properly

```javascript
// In preload.js
contextBridge.exposeInMainWorld('electronAPI', {
  saveFile: async (content, filePath) => {
    try {
      return await ipcRenderer.invoke('save-file', { content, filePath })
    } catch (error) {
      // Transform error for renderer
      throw new Error(`Failed to save file: ${error.message}`)
    }
  }
})

// In renderer.js
async function saveUserData() {
  try {
    const content = JSON.stringify(userData)
    const filePath = path.join(userDataPath, 'settings.json')
    
    await window.electronAPI.saveFile(content, filePath)
    showSuccessMessage('Settings saved successfully')
  } catch (error) {
    showErrorMessage(error.message)
    // Log error for debugging
    console.error('Save error:', error)
  }
}
```

### 4. Organize IPC Handlers by Domain

```javascript
// In main/handlers/file-handlers.js
const { ipcMain } = require('electron')
const fs = require('fs')

function registerFileHandlers() {
  ipcMain.handle('file:open', handleFileOpen)
  ipcMain.handle('file:save', handleFileSave)
  ipcMain.handle('file:delete', handleFileDelete)
}

async function handleFileOpen(event, path) {
  // Implementation
}

async function handleFileSave(event, { path, content }) {
  // Implementation
}

async function handleFileDelete(event, path) {
  // Implementation
}

module.exports = { registerFileHandlers }

// In main.js
const { registerFileHandlers } = require('./handlers/file-handlers')
const { registerAppHandlers } = require('./handlers/app-handlers')

app.whenReady().then(() => {
  registerFileHandlers()
  registerAppHandlers()
  // ...
})
```

## Security Considerations

1. **Never trust renderer input** - Always validate and sanitize
2. **Limit exposed APIs** - Only expose necessary functionality
3. **Use contextBridge** - Avoid direct ipcRenderer exposure
4. **Prevent prototype pollution** - Validate object structures
5. **Consider permissions** - Implement privilege checks for sensitive operations

## Performance Tips

1. **Batch messages** - Send multiple items in one message for large datasets
2. **Use binary formats** - Consider MessagePack or Protocol Buffers for large data
3. **Limit frequency** - Throttle high-frequency events
4. **Lazy load data** - Request data only when needed
5. **Clean up listeners** - Prevent memory leaks by removing unused listeners