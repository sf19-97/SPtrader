# Electron Security Best Practices

## Overview

Security is critical for Electron applications since they have access to both web and native capabilities. This guide covers essential security practices to protect your application from common vulnerabilities.

## Core Security Principles

1. **Only load trusted content** - Avoid loading remote content from untrusted sources
2. **Use context isolation** - Separate the renderer and preload script contexts
3. **Disable Node.js integration** - Prevent direct access to Node.js from renderer
4. **Enable sandbox** - Restrict capabilities in the renderer process
5. **Use secure IPC patterns** - Validate all data crossing process boundaries
6. **Keep Electron updated** - Security vulnerabilities are fixed in newer versions

## Security Checklist

### 1. BrowserWindow Configuration

```javascript
const mainWindow = new BrowserWindow({
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,       // REQUIRED: Isolate preload script
    nodeIntegration: false,       // REQUIRED: Disable Node.js in renderer
    sandbox: true,                // RECOMMENDED: Enable Chromium sandbox
    enableRemoteModule: false,    // REQUIRED: Disable remote module
    webSecurity: true,            // REQUIRED: Enable web security
    allowRunningInsecureContent: false,  // REQUIRED: Prevent mixed content
    webviewTag: false,            // RECOMMENDED: Disable webview tag
    navigateOnDragDrop: false     // RECOMMENDED: Prevent navigation on file drop
  }
})
```

### 2. Content Security Policy

```html
<!-- In HTML file -->
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'">
```

Or set via HTTP headers:

```javascript
// In main process
mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
  callback({
    responseHeaders: {
      ...details.responseHeaders,
      'Content-Security-Policy': [
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
      ]
    }
  })
})
```

### 3. Handle External Links Safely

```javascript
// In main process
const { shell } = require('electron')

// Set handler for link opening
mainWindow.webContents.setWindowOpenHandler(({ url }) => {
  // Check if URL is trusted
  if (isTrustedDomain(url)) {
    // Open URL in external browser
    shell.openExternal(url)
  } else {
    console.warn(`Blocked request to open untrusted URL: ${url}`)
  }
  // Prevent window creation
  return { action: 'deny' }
})

function isTrustedDomain(url) {
  try {
    const parsedUrl = new URL(url)
    const trustedDomains = ['example.com', 'github.com', 'electronjs.org']
    return trustedDomains.includes(parsedUrl.hostname)
  } catch (e) {
    return false
  }
}
```

### 4. Securely Load Remote Content

```javascript
// In main process
// Always prefer loading local content
mainWindow.loadFile('index.html')

// If remote content is necessary, validate URL and set CSP
function loadRemoteContent(url) {
  try {
    const parsedUrl = new URL(url)
    if (isAllowedDomain(parsedUrl.hostname)) {
      // Set strict CSP before loading remote content
      mainWindow.webContents.session.webRequest.onHeadersReceived(
        { urls: [url] },
        (details, callback) => {
          callback({
            responseHeaders: {
              ...details.responseHeaders,
              'Content-Security-Policy': ["default-src 'self'"]
            }
          })
        }
      )
      mainWindow.loadURL(url)
    } else {
      throw new Error(`Domain not allowed: ${parsedUrl.hostname}`)
    }
  } catch (error) {
    console.error('Error loading remote content:', error)
    mainWindow.loadFile('error.html')
  }
}
```

### 5. Validate IPC Messages

```javascript
// In main process
const { ipcMain } = require('electron')

// Validate incoming messages
ipcMain.handle('save-data', async (event, data) => {
  if (!data || typeof data !== 'object') {
    throw new Error('Invalid data format')
  }
  
  if (!data.filename || typeof data.filename !== 'string') {
    throw new Error('Invalid filename')
  }
  
  // Sanitize filename to prevent path traversal
  const sanitizedFilename = sanitizeFilename(data.filename)
  
  // Additional validation...
  
  // If all checks pass, proceed with saving
  return await saveDataToFile(sanitizedFilename, data.content)
})

function sanitizeFilename(filename) {
  // Remove path traversal characters
  return filename.replace(/[\/\\]/g, '')
}
```

### 6. Limit Session Permissions

```javascript
// In main process
// Restrict permissions
mainWindow.webContents.session.setPermissionRequestHandler(
  (webContents, permission, callback) => {
    const url = webContents.getURL()
    
    // Define allowed permissions
    const allowedPermissions = ['clipboard-read', 'clipboard-write']
    
    // Only allow certain permissions
    if (allowedPermissions.includes(permission)) {
      callback(true)
    } else {
      console.log(`Denied permission request: ${permission} for ${url}`)
      callback(false)
    }
  }
)
```

### 7. Update Checking and Integrity

```javascript
// In main process
// Use electron-updater for secure updates
const { autoUpdater } = require('electron-updater')

// Configure secure update
autoUpdater.setFeedURL({
  provider: 'github',
  owner: 'your-username',
  repo: 'your-repo',
  // Use private GitHub token for updates
  token: process.env.GITHUB_TOKEN
})

// Enable signature verification
autoUpdater.autoDownload = false
autoUpdater.allowDowngrade = false

autoUpdater.on('update-available', (info) => {
  // Notify user and get permission before downloading
  dialog.showMessageBox({
    type: 'info',
    title: 'Update Available',
    message: `Version ${info.version} is available. Download now?`,
    buttons: ['Yes', 'No']
  }).then(({ response }) => {
    if (response === 0) {
      autoUpdater.downloadUpdate()
    }
  })
})
```

### 8. Secure Data Storage

```javascript
// In main process
const { safeStorage } = require('electron')
const fs = require('fs')

// Encrypt sensitive data before storage
async function saveCredentials(username, password) {
  // Check if encryption is available
  if (safeStorage.isEncryptionAvailable()) {
    // Encrypt the password
    const encryptedPassword = safeStorage.encryptString(password)
    
    // Save to file
    fs.writeFileSync(
      path.join(app.getPath('userData'), 'credentials'),
      encryptedPassword
    )
    
    return true
  } else {
    throw new Error('Secure storage not available')
  }
}

// Decrypt data when needed
function getCredentials() {
  try {
    const encryptedPassword = fs.readFileSync(
      path.join(app.getPath('userData'), 'credentials')
    )
    
    // Decrypt the password
    const password = safeStorage.decryptString(encryptedPassword)
    return password
  } catch (error) {
    console.error('Failed to retrieve credentials:', error)
    return null
  }
}
```

## Common Vulnerabilities to Avoid

1. **XSS (Cross-Site Scripting)** - Never insert untrusted content into the DOM
2. **RCE (Remote Code Execution)** - Avoid `eval()`, `new Function()`, and dynamically requiring modules
3. **Path Traversal** - Sanitize file paths to prevent access outside intended directories
4. **Protocol Handler Exploitation** - Validate and sanitize custom protocol data
5. **Insecure Dependencies** - Regularly audit and update dependencies

## Resources

- [Electron Security Documentation](https://www.electronjs.org/docs/latest/tutorial/security)
- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)
- [Electron Security Checklist](https://github.com/doyensec/electronegativity/wiki/Checks)