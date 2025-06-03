# Electron Main Process Guide

## Overview

The main process in Electron is responsible for creating and managing BrowserWindow instances and various application events. It has full access to Node.js APIs and system resources.

## Key Concepts

### 1. Application Lifecycle

```javascript
const { app } = require('electron')

// When Electron has finished initialization
app.whenReady().then(() => {
  createWindow()
  
  // On macOS it's common to re-create a window when the dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
```

### 2. Creating Windows

```javascript
const { BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  // Load content
  mainWindow.loadFile('index.html')
  // Or load from URL
  // mainWindow.loadURL('https://example.com')
}
```

### 3. Security Best Practices

```javascript
const mainWindow = new BrowserWindow({
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,         // Isolate preload script from renderer
    nodeIntegration: false,         // Disable Node.js in renderer
    sandbox: true,                  // Enable Chromium sandbox
    enableRemoteModule: false,      // Disable remote module
    allowRunningInsecureContent: false  // Prevent loading HTTP content
  }
})
```

### 4. Inter-Process Communication (IPC)

```javascript
const { ipcMain } = require('electron')

// Handle requests from renderer
ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

// Handle one-way messages from renderer
ipcMain.on('log-message', (event, message) => {
  console.log('Received from renderer:', message)
})

// Send to a specific renderer
mainWindow.webContents.send('update-available', { version: '1.0.1' })
```

### 5. Application Menus

```javascript
const { Menu } = require('electron')

const template = [
  {
    label: 'File',
    submenu: [
      { label: 'New Window', click: () => createWindow() },
      { type: 'separator' },
      { role: 'quit' }
    ]
  },
  {
    label: 'Edit',
    submenu: [
      { role: 'undo' },
      { role: 'redo' },
      { type: 'separator' },
      { role: 'cut' },
      { role: 'copy' },
      { role: 'paste' }
    ]
  }
]

const menu = Menu.buildFromTemplate(template)
Menu.setApplicationMenu(menu)
```

### 6. Dialog Boxes

```javascript
const { dialog } = require('electron')

// Synchronous (blocks main process)
const result = dialog.showOpenDialogSync({
  properties: ['openFile', 'multiSelections']
})

// Asynchronous (recommended)
dialog.showOpenDialog({
  properties: ['openFile', 'multiSelections']
}).then(result => {
  if (!result.canceled) {
    // Process result.filePaths
  }
})
```

### 7. Handling App Updates

```javascript
const { autoUpdater } = require('electron-updater')

// Check for updates
autoUpdater.checkForUpdates()

autoUpdater.on('update-available', (info) => {
  mainWindow.webContents.send('update-available', info)
})

autoUpdater.on('update-downloaded', (info) => {
  mainWindow.webContents.send('update-downloaded', info)
})

// Install update when app is closed
autoUpdater.on('update-downloaded', () => {
  autoUpdater.quitAndInstall()
})
```

## Common Patterns

### Singleton Application Instance

```javascript
const gotTheLock = app.requestSingleInstanceLock()

if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    // Someone tried to run a second instance, we should focus our window
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })
}
```

### Graceful Shutdown

```javascript
let forceQuit = false

app.on('before-quit', () => {
  forceQuit = true
})

mainWindow.on('close', (event) => {
  if (!forceQuit) {
    event.preventDefault()
    // Save app state or confirm exit
    dialog.showMessageBox({
      type: 'question',
      buttons: ['Yes', 'No'],
      title: 'Confirm',
      message: 'Are you sure you want to quit?'
    }).then(result => {
      if (result.response === 0) {
        forceQuit = true
        app.quit()
      }
    })
  }
})
```

### Deep Linking

```javascript
// On Windows and Linux, this will be used if no other instance is running
app.on('open-url', (event, url) => {
  event.preventDefault()
  handleUrl(url)
})

// macOS requires additional setup
app.setAsDefaultProtocolClient('yourapp')

function handleUrl(url) {
  // Parse and handle the URL
  const urlObj = new URL(url)
  // Process urlObj.pathname, etc.
}
```

## Best Practices

1. **Keep the main process lean** - Offload CPU-intensive tasks to worker threads
2. **Avoid blocking operations** - Use async APIs whenever possible
3. **Handle errors and crashes** - Implement error reporting and crash recovery
4. **Securely expose APIs** - Validate all inputs from renderer processes
5. **Use contextBridge** - Expose functionality through a secure preload script
6. **Regularly update Electron** - Security patches are important
7. **Test thoroughly** - Main process bugs can crash the entire application