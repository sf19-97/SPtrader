# Electron Process Model

## Overview

Electron follows a multi-process architecture similar to Chromium, which helps improve security, stability, and performance. Understanding this model is fundamental for Electron development.

## Main Process vs. Renderer Process

### Main Process

The main process is the entry point of your application (specified in `main` field of `package.json`):

```javascript
// Example main.js (Main Process)
const { app, BrowserWindow } = require('electron')

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  })

  mainWindow.loadFile('index.html')
}

app.whenReady().then(createWindow)
```

**Responsibilities:**
- Application lifecycle management
- Native window creation and management
- System-level interactions
- Menu creation
- Integration with OS features
- Communication hub between renderers

**Features:**
- Full Node.js access
- Direct access to native APIs
- Single instance per app

### Renderer Process

Renderer processes display web content within windows:

```html
<!-- Example index.html (Renderer Process) -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Electron App</title>
</head>
<body>
  <h1>Hello from the renderer process!</h1>
  <script src="./renderer.js"></script>
</body>
</html>
```

```javascript
// Example renderer.js
// With contextIsolation enabled, you can't use Node.js directly
// You must use APIs exposed by the preload script
document.getElementById('btn').addEventListener('click', () => {
  window.electronAPI.doSomething()
})
```

**Responsibilities:**
- UI rendering
- User interaction
- DOM manipulation
- Web content execution

**Features:**
- Multiple instances (one per window/webview)
- Isolated from each other
- Uses Chromium's content module
- Limited access to Node.js (configurable)

## Process Communication

Since processes are isolated, they communicate via Inter-Process Communication (IPC):

### From Renderer to Main (One-way)

```javascript
// In preload.js
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  sendMessage: (message) => ipcRenderer.send('message', message)
})

// In renderer.js
document.getElementById('send-btn').addEventListener('click', () => {
  window.electronAPI.sendMessage('Hello from renderer!')
})

// In main.js
const { ipcMain } = require('electron')

ipcMain.on('message', (event, message) => {
  console.log('Received:', message)
})
```

### From Renderer to Main (Request-Response)

```javascript
// In preload.js
contextBridge.exposeInMainWorld('electronAPI', {
  getData: () => ipcRenderer.invoke('get-data')
})

// In renderer.js
async function fetchData() {
  const data = await window.electronAPI.getData()
  console.log(data)
}

// In main.js
ipcMain.handle('get-data', async () => {
  // Can be asynchronous
  return { result: 'success', items: [1, 2, 3] }
})
```

### From Main to Renderer

```javascript
// In main.js
mainWindow.webContents.send('update', { status: 'completed' })

// In preload.js
contextBridge.exposeInMainWorld('electronAPI', {
  onUpdate: (callback) => {
    ipcRenderer.on('update', (event, ...args) => callback(...args))
  }
})

// In renderer.js
window.electronAPI.onUpdate((data) => {
  console.log('Update received:', data)
})
```

## Additional Processes

### Utility Process

Introduced in newer Electron versions for background tasks:

```javascript
// In main.js
const { app, utilityProcess } = require('electron')
const path = require('path')

app.whenReady().then(() => {
  const utility = utilityProcess.fork(path.join(__dirname, 'utility.js'))
  
  utility.on('message', (message) => {
    console.log('Message from utility:', message)
  })
  
  utility.postMessage('start-task')
})

// In utility.js
process.parentPort.on('message', (message) => {
  if (message === 'start-task') {
    // Perform CPU-intensive task
    process.parentPort.postMessage('task-completed')
  }
})
```

### GPU Process

Managed by Chromium for hardware acceleration:
- Handles rendering and composition
- Offloads graphics tasks from renderer processes
- Automatically created as needed

## Process Architecture Diagram

```
+-----------------------------------+
|            Main Process           |
| (app.js / main.js - Node.js env)  |
+-----------------------------------+
            |         |
            |         |
            v         v
+---------------+ +---------------+
| Renderer Proc | | Renderer Proc |
| (Window 1)    | | (Window 2)    |
+---------------+ +---------------+
       |                 |
       v                 v
+-----------------------------------+
|             GPU Process           |
|      (Hardware acceleration)      |
+-----------------------------------+
            |
            v
+-----------------------------------+
|        Utility Processes          |
|     (Background operations)       |
+-----------------------------------+
```

## Security Considerations

### Process Isolation

Each process runs in its own memory space, which provides security benefits:
- Renderer process crashes don't affect the main process
- Malicious code in one renderer can't easily affect others
- Main process can validate all IPC communications

### Sandbox

Enable the sandbox for enhanced security:

```javascript
// In main.js
app.enableSandbox() // Enable for all renderers

// Or per-window
const win = new BrowserWindow({
  webPreferences: {
    sandbox: true
  }
})
```

## Process Management Best Practices

1. **Keep the main process lean**
   - Offload CPU-intensive work to utility processes
   - Avoid blocking the main process with long-running tasks

2. **Careful with shared resources**
   - Don't share objects directly between processes
   - Use IPC for communication

3. **Monitor process memory**
   ```javascript
   // In main.js
   setInterval(() => {
     const memoryInfo = process.getProcessMemoryInfo()
     console.log('Memory usage:', memoryInfo)
     
     // Get all process metrics
     const metrics = app.getAppMetrics()
     console.log('Process metrics:', metrics)
   }, 10000)
   ```

4. **Handle crashes gracefully**
   ```javascript
   // In main.js
   app.on('render-process-gone', (event, webContents, details) => {
     console.log('Renderer crashed:', details.reason)
     // Handle crash, possibly recreate window
   })
   ```

5. **Optimize IPC**
   - Batch messages when possible
   - Consider alternatives for large data transfers (e.g., shared memory)

## Process Model Limitations

1. **Overhead**
   - Multiple processes consume more memory
   - IPC adds latency compared to direct function calls

2. **Complexity**
   - Asynchronous communication can be harder to reason about
   - State management across processes requires careful design

3. **Native Modules**
   - Using native modules in renderer processes requires special handling
   - Consider keeping native modules in the main process only