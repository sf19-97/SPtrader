# Electron Performance Optimization Guide

## Overview

Electron applications can face performance challenges due to their multi-process architecture and Chromium base. This guide covers strategies to optimize Electron apps for speed, memory usage, and responsiveness.

## Key Performance Metrics

1. **Startup Time**: Time until the app is interactive
2. **Memory Usage**: RAM consumption across all processes
3. **CPU Usage**: Processing requirements during idle and active use
4. **Rendering Performance**: UI smoothness and frame rate
5. **Power Consumption**: Battery impact on mobile devices

## Startup Optimization

### 1. Minimize Main Process Work

The main process should do minimal work during startup:

```javascript
// AVOID during startup
app.whenReady().then(async () => {
  await heavyInitialization() // Blocks app startup
  createWindow()
})

// BETTER approach
app.whenReady().then(() => {
  createWindow() // Create window immediately
  
  // Defer non-critical work
  setTimeout(() => {
    heavyInitialization()
  }, 1000)
})
```

### 2. Lazy Load Modules

Only require modules when needed:

```javascript
// AVOID: Loading everything at startup
const { app, BrowserWindow, dialog, Menu, protocol, session } = require('electron')
const heavyModule1 = require('./heavy-module-1')
const heavyModule2 = require('./heavy-module-2')

// BETTER: Lazy load modules when needed
const { app, BrowserWindow } = require('electron')

function showDialog() {
  // Only load dialog module when needed
  const { dialog } = require('electron')
  dialog.showOpenDialog({ properties: ['openFile'] })
}

async function useHeavyModule() {
  // Dynamically import modules
  const heavyModule = await import('./heavy-module')
  return heavyModule.doSomething()
}
```

### 3. Optimize Preload Scripts

Keep preload scripts small and efficient:

```javascript
// AVOID: Loading everything in preload
const { ipcRenderer, shell, clipboard } = require('electron')
const fs = require('fs')
const path = require('path')
const crypto = require('crypto')

// BETTER: Only expose what's needed
const { contextBridge, ipcRenderer } = require('electron')

// Expose minimal API surface
contextBridge.exposeInMainWorld('electronAPI', {
  openFile: () => ipcRenderer.invoke('dialog:openFile')
})
```

### 4. Use `ready-to-show` Event

Show the window only when content is ready:

```javascript
const win = new BrowserWindow({
  show: false, // Don't show immediately
  webPreferences: { /* ... */ }
})

win.loadFile('index.html')

// Show window when content is ready to prevent flickering
win.once('ready-to-show', () => {
  win.show()
})
```

### 5. Defer Renderer Initialization

Use progressive loading in the renderer:

```javascript
// In renderer.js
document.addEventListener('DOMContentLoaded', () => {
  // Show UI immediately
  document.querySelector('#app').style.display = 'block'
  
  // Defer non-critical initialization
  requestIdleCallback(() => {
    initializeNonCriticalFeatures()
  })
})

// For frameworks like React
function App() {
  const [isReady, setIsReady] = useState(false)
  
  useEffect(() => {
    // Show skeleton immediately
    
    // Load full app in background
    setTimeout(() => {
      setIsReady(true)
    }, 100)
  }, [])
  
  return isReady ? <FullApp /> : <Skeleton />
}
```

## Memory Optimization

### 1. Monitor Memory Usage

```javascript
// In main process, periodically check memory
setInterval(() => {
  const memoryInfo = process.getProcessMemoryInfo()
  console.log('Memory usage:', {
    rss: `${Math.round(memoryInfo.rss / 1024 / 1024)} MB`,
    heapTotal: `${Math.round(memoryInfo.heapTotal / 1024 / 1024)} MB`,
    heapUsed: `${Math.round(memoryInfo.heapUsed / 1024 / 1024)} MB`,
    external: `${Math.round(memoryInfo.external / 1024 / 1024)} MB`
  })
}, 10000)

// Get memory for all processes
app.getAppMetrics().forEach(metric => {
  console.log(`Process: ${metric.type}, Memory: ${metric.memory.workingSetSize / 1024 / 1024} MB`)
})
```

### 2. Manage Window Lifecycle

Properly dispose of windows and their resources:

```javascript
// Store windows in a Map or Set
const windows = new Set()

function createWindow() {
  const win = new BrowserWindow({ /* ... */ })
  windows.add(win)
  
  win.on('closed', () => {
    windows.delete(win)
  })
  
  return win
}

// Explicitly close windows when no longer needed
function closeWindowsForUser(userId) {
  for (const win of windows) {
    if (win.userId === userId) {
      win.close()
    }
  }
}
```

### 3. Avoid Memory Leaks

Common causes of memory leaks:

```javascript
// AVOID: Event listener leaks
function setupWindow(win) {
  // This listener is never removed!
  ipcMain.on('event', handleEvent)
}

// BETTER: Track and remove listeners
function setupWindow(win) {
  const handleEvent = (event, ...args) => {
    // Handle event
  }
  
  ipcMain.on('event', handleEvent)
  
  win.on('closed', () => {
    // Clean up when window closes
    ipcMain.removeListener('event', handleEvent)
  })
}

// AVOID: Circular references
function createObjects() {
  const parent = {}
  const child = {}
  
  parent.child = child
  child.parent = parent // Circular reference
  
  return parent
}

// BETTER: Use weak references when appropriate
function createObjects() {
  const parent = {}
  const child = {}
  
  parent.child = child
  child.parentRef = new WeakRef(parent) // Weak reference
  
  return parent
}
```

### 4. Use Proper Data Structures

Choose appropriate data structures for your use case:

```javascript
// For large datasets, consider specialized libraries
// or virtualization techniques

// AVOID: Loading everything in memory
function loadAllRecords() {
  return database.fetchAllRecords() // Could be millions!
}

// BETTER: Paginate and virtualize
function loadRecordPage(page, pageSize) {
  return database.fetchRecordPage(page, pageSize)
}

// In the renderer, use virtualized lists
// Example with react-window
import { FixedSizeList } from 'react-window'

function VirtualizedList({ items }) {
  return (
    <FixedSizeList
      height={500}
      width={500}
      itemCount={items.length}
      itemSize={50}
    >
      {({ index, style }) => (
        <div style={style}>
          {items[index].name}
        </div>
      )}
    </FixedSizeList>
  )
}
```

## Renderer Process Optimization

### 1. Minimize DOM Operations

DOM operations are expensive:

```javascript
// AVOID: Frequent DOM updates
function updateCounter(count) {
  for (let i = 0; i < count; i++) {
    document.getElementById('counter').textContent = i
  }
}

// BETTER: Batch DOM updates
function updateCounter(count) {
  requestAnimationFrame(() => {
    document.getElementById('counter').textContent = count
  })
}

// EVEN BETTER: Use virtual DOM (React, Vue, etc.)
function Counter({ count }) {
  return <div id="counter">{count}</div>
}
```

### 2. Optimize Rendering

Prevent layout thrashing and ensure smooth animations:

```javascript
// AVOID: Reading and writing layout properties repeatedly
function resizeElements() {
  const elements = document.querySelectorAll('.box')
  
  elements.forEach(el => {
    const height = el.offsetHeight // Read
    el.style.width = `${height * 2}px` // Write
    const newWidth = el.offsetWidth // Read (triggers layout recalc)
    el.style.height = `${newWidth / 2}px` // Write (triggers layout recalc)
  })
}

// BETTER: Batch reads and writes
function resizeElements() {
  const elements = document.querySelectorAll('.box')
  const heights = []
  
  // Batch all reads
  elements.forEach(el => {
    heights.push(el.offsetHeight)
  })
  
  // Batch all writes
  elements.forEach((el, i) => {
    const height = heights[i]
    el.style.width = `${height * 2}px`
    el.style.height = `${height}px`
  })
}
```

### 3. Web Workers for CPU-Intensive Tasks

Offload heavy work to Web Workers:

```javascript
// In renderer.js
const worker = new Worker('worker.js')

// Send data to worker
worker.postMessage({
  action: 'process',
  data: largeDataset
})

// Receive results
worker.onmessage = (event) => {
  displayResults(event.data)
}

// In worker.js
self.onmessage = (event) => {
  if (event.data.action === 'process') {
    // Perform CPU-intensive work
    const result = performHeavyCalculation(event.data.data)
    
    // Send result back to main thread
    self.postMessage(result)
  }
}
```

### 4. Use GPU Acceleration Wisely

Leverage the GPU but be careful with overuse:

```css
/* GOOD: Hardware accelerated properties */
.smooth-animation {
  transform: translateZ(0); /* Hint for compositing layer */
  transition: transform 0.3s ease;
  will-change: transform; /* Use sparingly! */
}

/* AVOID: Too many composite layers */
.every-element {
  transform: translateZ(0); /* Don't do this for everything! */
}
```

## IPC Optimization

### 1. Minimize IPC Message Size

Large IPC messages can impact performance:

```javascript
// AVOID: Sending large objects
ipcRenderer.send('data', { 
  hugeDataset: veryLargeArray, 
  entireDom: document.querySelector('html').innerHTML 
})

// BETTER: Send only what's needed
ipcRenderer.send('data', {
  id: datasetId,
  summary: generateSummary(veryLargeArray)
})

// ALTERNATIVE: For large data, use storage or shared memory
function shareLargeData(data) {
  const id = `data-${Date.now()}`
  localStorage.setItem(id, JSON.stringify(data))
  ipcRenderer.send('data-ready', { id })
}
```

### 2. Batch IPC Messages

Combine multiple messages when possible:

```javascript
// AVOID: Multiple messages
function updateUI(data) {
  ipcRenderer.send('update-title', data.title)
  ipcRenderer.send('update-status', data.status)
  ipcRenderer.send('update-count', data.count)
}

// BETTER: Batch updates
function updateUI(data) {
  ipcRenderer.send('update-ui', {
    title: data.title,
    status: data.status,
    count: data.count
  })
}
```

### 3. Use Synchronous IPC Sparingly

Synchronous IPC blocks the renderer:

```javascript
// AVOID: Synchronous IPC
function getUserConfig() {
  // Blocks renderer until response is received
  return ipcRenderer.sendSync('get-user-config')
}

// BETTER: Asynchronous IPC
async function getUserConfig() {
  return await ipcRenderer.invoke('get-user-config')
}
```

## Process Management

### 1. Limit Process Count

Each BrowserWindow creates a new renderer process:

```javascript
// AVOID: Creating too many windows
function showMultipleItems(items) {
  items.forEach(item => {
    new BrowserWindow({ width: 400, height: 300 })
      .loadURL(`item.html?id=${item.id}`)
  })
}

// BETTER: Reuse windows or use tabs/panels
function showMultipleItems(items) {
  const win = new BrowserWindow({ width: 800, height: 600 })
  win.loadURL('items.html')
  
  // Send all items to single window
  win.webContents.on('did-finish-load', () => {
    win.webContents.send('items', items)
  })
}
```

### 2. Control Background Processes

Manage processes for background work:

```javascript
// Use a shared worker process for background tasks
let backgroundWindow = null

function getBackgroundWindow() {
  if (backgroundWindow === null || backgroundWindow.isDestroyed()) {
    backgroundWindow = new BrowserWindow({
      show: false,
      webPreferences: { nodeIntegration: true }
    })
    backgroundWindow.loadFile('background.html')
  }
  return backgroundWindow
}

// Run tasks in the background
function runBackgroundTask(taskData) {
  const win = getBackgroundWindow()
  win.webContents.send('run-task', taskData)
}
```

## Tools for Performance Analysis

### 1. Chrome DevTools

```javascript
// Open DevTools for performance profiling
mainWindow.webContents.openDevTools()

// In renderer, record performance
console.profile('Rendering')
renderComplexUI()
console.profileEnd('Rendering')

// Memory snapshots
// In DevTools: Memory tab > Take heap snapshot
```

### 2. Custom Performance Monitoring

```javascript
// Measure startup phases
const startTime = Date.now()

app.whenReady().then(() => {
  console.log(`App ready time: ${Date.now() - startTime}ms`)
  
  const win = new BrowserWindow({ /* ... */ })
  win.loadFile('index.html')
  
  win.webContents.once('did-finish-load', () => {
    console.log(`Page loaded time: ${Date.now() - startTime}ms`)
  })
  
  win.once('ready-to-show', () => {
    console.log(`Ready to show time: ${Date.now() - startTime}ms`)
    win.show()
  })
})

// Track slow operations
function trackOperation(name, operation) {
  const start = performance.now()
  const result = operation()
  const duration = performance.now() - start
  
  if (duration > 100) {
    console.warn(`Slow operation: ${name} took ${duration.toFixed(2)}ms`)
  }
  
  return result
}
```

## Best Practices Summary

1. **Start fast, load less** - Prioritize fast startup, defer non-critical work
2. **Monitor memory** - Track memory usage across processes
3. **Optimize IPC** - Minimize message size and frequency
4. **Use workers** - Offload CPU-intensive tasks
5. **Virtualize data** - Don't render what's not visible
6. **Batch operations** - Group reads/writes for DOM and IPC
7. **Profile regularly** - Use Chrome DevTools to identify bottlenecks
8. **Clean up resources** - Remove event listeners, close windows properly
9. **Be mindful of platform** - Mobile devices need more optimization
10. **Test on target hardware** - Performance varies across devices