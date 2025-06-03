# Electron WebContents Guide

## Overview

`WebContents` is one of the most powerful objects in Electron, representing the content of a web page. It's used to control and interact with the renderer process, handle web page events, and manage navigation.

## Key Concepts

### 1. Accessing WebContents

WebContents can be accessed from a BrowserWindow:

```javascript
// From a BrowserWindow instance
const { webContents } = browserWindow

// From the webContents module
const { webContents } = require('electron')
const allContents = webContents.getAllWebContents()
```

### 2. Page Lifecycle Events

Monitor and respond to page events:

```javascript
// In main process
browserWindow.webContents.on('did-finish-load', () => {
  console.log('Page has finished loading')
})

browserWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
  console.error(`Failed to load: ${errorDescription} (${errorCode})`)
})

browserWindow.webContents.on('dom-ready', () => {
  console.log('DOM is ready')
})

browserWindow.webContents.on('page-title-updated', (event, title) => {
  console.log(`Title changed to: ${title}`)
})
```

### 3. Navigation Control

Manage page navigation:

```javascript
// Navigate to a URL
browserWindow.webContents.loadURL('https://example.com')

// Navigate to a local file
browserWindow.webContents.loadFile('index.html')

// Check if can go back/forward
const canGoBack = browserWindow.webContents.canGoBack()
const canGoForward = browserWindow.webContents.canGoForward()

// Navigate back/forward
if (canGoBack) browserWindow.webContents.goBack()
if (canGoForward) browserWindow.webContents.goForward()

// Reload the page
browserWindow.webContents.reload()
browserWindow.webContents.reloadIgnoringCache() // Hard reload

// Stop loading
browserWindow.webContents.stop()
```

### 4. Communication with Renderer

Send messages to the renderer process:

```javascript
// Send a message to the renderer
browserWindow.webContents.send('update-counter', { count: 5 })

// With multiple arguments
browserWindow.webContents.send('data-update', 'users', { users: [...] })
```

### 5. Content Manipulation

Execute JavaScript in the renderer:

```javascript
// Execute JavaScript in the page context
browserWindow.webContents.executeJavaScript(`
  document.querySelector('h1').textContent = 'Updated Title';
  console.log('Title updated');
`)

// With a return value
const result = await browserWindow.webContents.executeJavaScript(`
  document.title;
`)
console.log(`Page title is: ${result}`)

// Insert CSS
browserWindow.webContents.insertCSS(`
  body { 
    background-color: #f0f0f0; 
    color: #333; 
  }
`)
```

### 6. Page Printing and PDF Generation

Print or generate PDFs from web content:

```javascript
// Print the page
browserWindow.webContents.print({ silent: false, printBackground: true })

// Generate PDF
const pdfOptions = {
  marginsType: 0,
  pageSize: 'A4',
  printBackground: true,
  landscape: false
}

browserWindow.webContents.printToPDF(pdfOptions).then(data => {
  // data is a Buffer containing the PDF
  fs.writeFile('page.pdf', data, (error) => {
    if (error) throw error
    console.log('PDF saved successfully')
  })
}).catch(error => {
  console.error('Failed to generate PDF:', error)
})
```

### 7. DevTools Integration

Manage DevTools for debugging:

```javascript
// Open DevTools
browserWindow.webContents.openDevTools()

// Open DevTools with specific mode
browserWindow.webContents.openDevTools({ mode: 'detach' }) // 'right', 'bottom', 'undocked'

// Close DevTools
browserWindow.webContents.closeDevTools()

// Check if DevTools is open
const isDevToolsOpen = browserWindow.webContents.isDevToolsOpened()

// Focus DevTools
if (isDevToolsOpen) {
  browserWindow.webContents.devToolsWebContents.focus()
}
```

### 8. Security Controls

Enhance security with WebContents:

```javascript
// Set Content Security Policy
browserWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
  callback({
    responseHeaders: {
      ...details.responseHeaders,
      'Content-Security-Policy': ['default-src \'self\'']
    }
  })
})

// Validate navigation (prevent phishing)
browserWindow.webContents.on('will-navigate', (event, url) => {
  const parsedUrl = new URL(url)
  if (!isTrustedDomain(parsedUrl.hostname)) {
    event.preventDefault()
    console.warn(`Blocked navigation to untrusted domain: ${url}`)
  }
})

// Control new window creation
browserWindow.webContents.setWindowOpenHandler(({ url }) => {
  if (isTrustedDomain(new URL(url).hostname)) {
    // Allow opening in external browser
    shell.openExternal(url)
  }
  // Prevent window creation
  return { action: 'deny' }
})
```

## BrowserView Integration

BrowserViews are an alternative to BrowserWindows for displaying web content:

### 1. Creating a BrowserView

```javascript
const { BrowserView, BrowserWindow } = require('electron')
const mainWindow = new BrowserWindow({ width: 800, height: 600 })

// Create a BrowserView
const view = new BrowserView({
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false
  }
})

// Add it to the window
mainWindow.setBrowserView(view)

// Position and resize the view
view.setBounds({ x: 0, y: 0, width: 800, height: 600 })

// Navigate the view
view.webContents.loadURL('https://electronjs.org')
```

### 2. Managing Multiple Views

```javascript
const { BrowserView, BrowserWindow } = require('electron')
const mainWindow = new BrowserWindow({ width: 1200, height: 800 })

// Create multiple views
const leftView = new BrowserView()
const rightView = new BrowserView()

// Add views to the window
mainWindow.addBrowserView(leftView)
mainWindow.addBrowserView(rightView)

// Position views side by side
leftView.setBounds({ x: 0, y: 0, width: 600, height: 800 })
rightView.setBounds({ x: 600, y: 0, width: 600, height: 800 })

// Navigate views
leftView.webContents.loadURL('https://example.com')
rightView.webContents.loadFile('local-page.html')

// Remove a view
mainWindow.removeBrowserView(leftView)

// Get all views
const allViews = mainWindow.getBrowserViews()
```

### 3. Handling BrowserView Events

```javascript
// Listen for events on the view's webContents
view.webContents.on('did-finish-load', () => {
  console.log('View finished loading')
})

view.webContents.on('page-title-updated', (event, title) => {
  // Update UI to show the title
  mainWindow.setTitle(`View: ${title}`)
})

// Communication with the view
view.webContents.send('message-to-view', { data: 'some data' })
```

## Common Patterns

### 1. User Session Management

```javascript
// Create a persistent session
const { session } = require('electron')
const persistentSession = session.fromPartition('persist:user-session')

// Create a window with the persistent session
const window = new BrowserWindow({
  webPreferences: {
    session: persistentSession
  }
})

// Clear session data
window.webContents.session.clearStorageData({
  storages: ['cookies', 'localStorage', 'sessionStorage', 'cache']
})
```

### 2. Content Filtering and Modification

```javascript
// Modify request headers
window.webContents.session.webRequest.onBeforeSendHeaders(
  { urls: ['*://*/*'] },
  (details, callback) => {
    details.requestHeaders['User-Agent'] = 'Custom User Agent'
    callback({ requestHeaders: details.requestHeaders })
  }
)

// Block specific content
window.webContents.session.webRequest.onBeforeRequest(
  { urls: ['*://*.ads.example.com/*'] },
  (details, callback) => {
    callback({ cancel: true })
  }
)

// Inject scripts into specific pages
window.webContents.on('did-finish-load', () => {
  if (window.webContents.getURL().includes('example.com')) {
    window.webContents.executeJavaScript(`
      // Add custom functionality to the page
      document.body.style.background = '#f0f0f0';
    `)
  }
})
```

### 3. Custom Protocol Handling

```javascript
// Register a custom protocol
const { protocol } = require('electron')
protocol.registerFileProtocol('app', (request, callback) => {
  const url = request.url.substr(6) // Remove 'app://'
  callback({ path: path.join(__dirname, 'app', url) })
})

// Use in WebContents
window.webContents.loadURL('app://index.html')
```

### 4. Responsive UI Updates

```javascript
// Automatically resize WebContents when window size changes
mainWindow.on('resize', () => {
  const [width, height] = mainWindow.getContentSize()
  view.setBounds({ x: 0, y: 0, width, height })
})

// Create split layouts
function createSplitLayout(mainWindow, ratio = 0.5) {
  const [width, height] = mainWindow.getContentSize()
  const leftWidth = Math.floor(width * ratio)
  
  leftView.setBounds({ x: 0, y: 0, width: leftWidth, height })
  rightView.setBounds({ x: leftWidth, y: 0, width: width - leftWidth, height })
}
```

## Best Practices

1. **Limit concurrent WebContents** - Each uses significant memory
2. **Dispose properly** - Destroy WebContents when no longer needed
3. **Control permissions** - Set permission handlers to limit capabilities
4. **Validate URLs** - Always check URLs before navigation
5. **Handle errors** - Listen for load failures and other errors
6. **Monitor memory usage** - Watch for memory leaks with many WebContents
7. **Secure content** - Apply Content Security Policy
8. **Control navigation** - Handle `will-navigate` and `will-redirect` events