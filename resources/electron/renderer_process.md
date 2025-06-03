# Electron Renderer Process Guide

## Overview

The renderer process in Electron is responsible for displaying the user interface of your application. Each renderer process is a separate Chromium browser instance with its own JavaScript context.

## Key Concepts

### 1. Process Isolation

Renderer processes run in a sandboxed environment with context isolation. This means:

- No direct access to Node.js APIs by default
- Needs a preload script to communicate with the main process
- Cannot directly access native OS functionality

### 2. Communication with Main Process

```javascript
// In renderer process
// Using contextBridge exposed API (recommended)
window.electronAPI.sendMessage('Hello from renderer')

window.electronAPI.onUpdateAvailable((event, info) => {
  console.log('Update available:', info.version)
})

// Get a response from the main process
async function getAppVersion() {
  const version = await window.electronAPI.getAppVersion()
  console.log('App version:', version)
}
```

### 3. Web Technologies

Renderer processes support modern web technologies:

- HTML5, CSS3, and JavaScript (ES6+)
- Web Components and Shadow DOM
- Canvas, WebGL, and WebGPU
- Modern frameworks like React, Vue, or Angular

```javascript
// Example using React
import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom'

function App() {
  const [appVersion, setAppVersion] = useState(null)
  
  useEffect(() => {
    async function fetchVersion() {
      const version = await window.electronAPI.getAppVersion()
      setAppVersion(version)
    }
    fetchVersion()
  }, [])
  
  return (
    <div>
      <h1>Electron App</h1>
      {appVersion && <p>Version: {appVersion}</p>}
    </div>
  )
}

ReactDOM.render(<App />, document.getElementById('root'))
```

### 4. Performance Considerations

```javascript
// Use requestAnimationFrame for animations
function animate() {
  // Update UI
  requestAnimationFrame(animate)
}
requestAnimationFrame(animate)

// Use requestIdleCallback for non-critical work
requestIdleCallback(() => {
  // Do non-urgent background work
}, { timeout: 1000 })

// Web Workers for CPU-intensive tasks
const worker = new Worker('worker.js')
worker.postMessage({ data: complexData })
worker.onmessage = (event) => {
  const result = event.data
  // Update UI with result
}
```

### 5. Native Look and Feel

```css
/* Use system fonts */
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 
    'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 
    'Open Sans', 'Helvetica Neue', sans-serif;
}

/* System-specific styles */
@media (prefers-color-scheme: dark) {
  body {
    background-color: #222;
    color: #eee;
  }
}

@media (prefers-color-scheme: light) {
  body {
    background-color: #fff;
    color: #222;
  }
}
```

## Common Patterns

### 1. Asynchronous API Calls

```javascript
// Using async/await with IPC
async function getUserData() {
  try {
    const userData = await window.electronAPI.getUserData()
    displayUserData(userData)
  } catch (error) {
    showError('Failed to get user data: ' + error.message)
  }
}

// Handling streams of data
let dataListener
function startDataStream() {
  window.electronAPI.startDataStream()
  
  dataListener = (event, data) => {
    updateChart(data)
  }
  
  window.electronAPI.onDataReceived(dataListener)
}

function stopDataStream() {
  window.electronAPI.stopDataStream()
  window.electronAPI.removeListener('data-received', dataListener)
}
```

### 2. Managing Window State

```javascript
// Save window position and size before closing
window.addEventListener('beforeunload', () => {
  const bounds = window.electronAPI.getCurrentWindowBounds()
  localStorage.setItem('windowBounds', JSON.stringify(bounds))
})

// Restore window state on load
document.addEventListener('DOMContentLoaded', () => {
  const savedBounds = localStorage.getItem('windowBounds')
  if (savedBounds) {
    window.electronAPI.setWindowBounds(JSON.parse(savedBounds))
  }
})
```

### 3. Drag and Drop

```javascript
const dropZone = document.getElementById('drop-zone')

dropZone.addEventListener('dragover', (event) => {
  event.preventDefault()
  event.stopPropagation()
  dropZone.classList.add('drag-over')
})

dropZone.addEventListener('dragleave', (event) => {
  event.preventDefault()
  event.stopPropagation()
  dropZone.classList.remove('drag-over')
})

dropZone.addEventListener('drop', async (event) => {
  event.preventDefault()
  event.stopPropagation()
  dropZone.classList.remove('drag-over')
  
  const files = Array.from(event.dataTransfer.files)
  const filePaths = files.map(file => file.path)
  
  await window.electronAPI.processFiles(filePaths)
})
```

### 4. Virtual DOM Rendering

```javascript
// Using lightweight virtual DOM library
import { h, render, Component } from 'preact'

class App extends Component {
  state = { data: [] }
  
  async componentDidMount() {
    // Set up IPC listeners
    window.electronAPI.onNewData((event, newData) => {
      this.setState(prevState => ({
        data: [...prevState.data, newData]
      }))
    })
    
    // Initial data load
    const initialData = await window.electronAPI.getInitialData()
    this.setState({ data: initialData })
  }
  
  render() {
    const { data } = this.state
    return (
      <div class="app">
        <header>
          <h1>Data Viewer</h1>
        </header>
        <main>
          <DataTable data={data} />
        </main>
      </div>
    )
  }
}

render(<App />, document.body)
```

## Best Practices

1. **Don't use remote module** - It has security and performance implications
2. **Validate all inputs** - Never trust data from untrusted sources
3. **Use responsive design** - Windows can be resized by users
4. **Lazy load resources** - Improve startup performance
5. **Handle connectivity issues** - Offline support and retry mechanisms
6. **Optimize memory usage** - Use pagination, virtualization for large data sets
7. **Implement accessibility** - Support keyboard navigation and screen readers
8. **Follow platform conventions** - Respect system preferences and behaviors
9. **Cache results** - Store non-sensitive data for faster startup
10. **Use devtools** - Profile performance and debug issues