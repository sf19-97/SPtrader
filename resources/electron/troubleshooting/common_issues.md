# Common Electron Issues and Solutions

## Startup Issues

### White Screen / Blank Window

**Problem:** Application opens but shows a blank white window.

**Possible Causes:**
1. Content failed to load
2. JavaScript errors in renderer process
3. Incorrect path to HTML file
4. Missing dependencies

**Solutions:**

1. **Check console for errors:**
   ```javascript
   // In main.js
   mainWindow.webContents.openDevTools()
   ```

2. **Verify file paths:**
   ```javascript
   // Use absolute paths with path.join
   mainWindow.loadFile(path.join(__dirname, 'index.html'))
   ```

3. **Add error handlers:**
   ```javascript
   // In main.js
   mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
     console.error('Failed to load:', errorCode, errorDescription)
     mainWindow.loadFile(path.join(__dirname, 'error.html'))
   })
   ```

4. **Wait for ready-to-show:**
   ```javascript
   mainWindow = new BrowserWindow({
     show: false,
     // other options...
   })
   
   mainWindow.once('ready-to-show', () => {
     mainWindow.show()
   })
   ```

### Application Crashes on Startup

**Problem:** Application crashes immediately or soon after starting.

**Possible Causes:**
1. Native module compatibility issues
2. Misconfigured BrowserWindow options
3. Resource access errors

**Solutions:**

1. **Check error logs:**
   ```bash
   # Windows
   %USERPROFILE%\AppData\Roaming\[AppName]\logs
   
   # macOS
   ~/Library/Logs/[AppName]
   
   # Linux
   ~/.config/[AppName]/logs
   ```

2. **Rebuild native modules:**
   ```bash
   # Using electron-rebuild
   npx electron-rebuild
   
   # Or using electron-builder
   npx electron-builder install-app-deps
   ```

3. **Start with minimal configuration:**
   ```javascript
   // Create bare minimum window without extra options
   const mainWindow = new BrowserWindow({
     width: 800,
     height: 600
   })
   
   mainWindow.loadFile('index.html')
   ```

## IPC Communication Issues

### No Response from Main Process

**Problem:** Renderer process sends messages but gets no response from main process.

**Possible Causes:**
1. IPC channel name mismatch
2. Using `ipcMain.on` instead of `ipcMain.handle` for responses
3. Context isolation configuration issues

**Solutions:**

1. **Check channel names carefully:**
   ```javascript
   // In main.js
   ipcMain.handle('get-data', async () => {
     // Ensure this EXACT channel name is used in preload.js
     return { result: 'success' }
   })
   
   // In preload.js
   contextBridge.exposeInMainWorld('electronAPI', {
     getData: () => ipcRenderer.invoke('get-data') // Must match exactly
   })
   ```

2. **Use `handle` for response patterns:**
   ```javascript
   // WRONG - will not return a response to invoke
   ipcMain.on('get-data', (event) => {
     event.returnValue = { result: 'success' }
   })
   
   // CORRECT - works with invoke
   ipcMain.handle('get-data', async () => {
     return { result: 'success' }
   })
   ```

3. **Check context isolation setup:**
   ```javascript
   // In main.js - ensure these options are correct
   const mainWindow = new BrowserWindow({
     webPreferences: {
       preload: path.join(__dirname, 'preload.js'),
       contextIsolation: true,  // Must be true
       nodeIntegration: false
     }
   })
   ```

### Context Isolation Issues

**Problem:** Cannot access exposed APIs from the renderer.

**Possible Causes:**
1. Missing or incorrect `contextBridge.exposeInMainWorld` call
2. Accessing API incorrectly in renderer
3. Type errors in API usage

**Solutions:**

1. **Verify API exposure:**
   ```javascript
   // In preload.js
   contextBridge.exposeInMainWorld('electronAPI', {
     // Methods must be properties of the exposed object
     doSomething: () => ipcRenderer.invoke('do-something')
   })
   
   // Then in renderer.js
   // CORRECT:
   window.electronAPI.doSomething()
   
   // WRONG:
   window.doSomething()
   window.electronAPI()
   ```

2. **Debug exposed APIs:**
   ```javascript
   // In renderer.js
   console.log('Available APIs:', window.electronAPI)
   // Check that methods exist and are functions
   ```

3. **Fix type issues:**
   ```javascript
   // In preload.js - ensure correct function signatures
   contextBridge.exposeInMainWorld('electronAPI', {
     // Method expects arguments
     saveFile: (content, path) => ipcRenderer.invoke('save-file', { content, path })
   })
   
   // In renderer.js - call with correct arguments
   window.electronAPI.saveFile(content, filePath)
   ```

## Security and Permissions

### Permissions Denied Errors

**Problem:** Application cannot access certain system features (camera, file system, etc.).

**Possible Causes:**
1. Missing permissions
2. Sandbox restrictions
3. Permission handler not configured

**Solutions:**

1. **Configure permission handler:**
   ```javascript
   // In main.js
   mainWindow.webContents.session.setPermissionRequestHandler(
     (webContents, permission, callback) => {
       // Allow all permissions from our origin
       const requestingOrigin = new URL(webContents.getURL()).origin
       const isOurOrigin = requestingOrigin === 'file://' || 
                          requestingOrigin === 'https://yourapp.com'
       
       if (isOurOrigin) {
         // Grant permission
         callback(true)
       } else {
         // Deny permission
         callback(false)
       }
     }
   )
   ```

2. **Handle specific permissions:**
   ```javascript
   // Grant only specific permissions
   mainWindow.webContents.session.setPermissionRequestHandler(
     (webContents, permission, callback) => {
       const allowedPermissions = ['media', 'notifications', 'clipboard-read']
       callback(allowedPermissions.includes(permission))
     }
   )
   ```

3. **Disable sandbox for specific cases:**
   ```javascript
   // Only if absolutely necessary
   const mainWindow = new BrowserWindow({
     webPreferences: {
       sandbox: false, // Use with caution!
       preload: path.join(__dirname, 'preload.js'),
       contextIsolation: true
     }
   })
   ```

### "Not allowed to load local resource" Errors

**Problem:** Cannot load local files or resources in the renderer.

**Possible Causes:**
1. Security restrictions preventing file access
2. Incorrect file paths
3. Content Security Policy blocking local resources

**Solutions:**

1. **Use proper protocol for local resources:**
   ```javascript
   // In main.js - serve local files via file:// protocol
   mainWindow.loadFile(path.join(__dirname, 'index.html'))
   
   // In renderer - use relative paths for resources
   const image = document.createElement('img')
   image.src = './images/logo.png' // Relative to the HTML file
   ```

2. **Configure CSP to allow local resources:**
   ```html
   <!-- In HTML head -->
   <meta http-equiv="Content-Security-Policy" 
         content="default-src 'self'; img-src 'self' data:;">
   ```

3. **Use protocol handler for custom schemes:**
   ```javascript
   // In main.js
   const { protocol } = require('electron')
   
   app.whenReady().then(() => {
     protocol.registerFileProtocol('app', (request, callback) => {
       const url = request.url.substr(6) // Remove 'app://'
       callback({ path: path.join(__dirname, url) })
     })
     
     // Then load using this protocol
     mainWindow.loadURL('app://index.html')
   })
   ```

## Performance Issues

### High CPU/Memory Usage

**Problem:** Application consumes excessive CPU or memory resources.

**Possible Causes:**
1. Memory leaks in renderer process
2. Unoptimized rendering
3. Background processes running unchecked

**Solutions:**

1. **Monitor and identify issues:**
   ```javascript
   // In main.js
   setInterval(() => {
     const memoryInfo = process.getProcessMemoryInfo()
     const cpuUsage = process.getCPUUsage()
     console.log('Memory usage:', memoryInfo)
     console.log('CPU usage:', cpuUsage)
   }, 10000)
   ```

2. **Optimize DOM updates:**
   ```javascript
   // Use requestAnimationFrame for visual updates
   function updateUI() {
     // Batch DOM operations
     requestAnimationFrame(() => {
       // Update DOM here
     })
   }
   
   // Use virtualization for long lists
   // Consider libraries like react-window or react-virtualized
   ```

3. **Clean up event listeners:**
   ```javascript
   // Manage listeners properly
   const handler = () => { /* ... */ }
   element.addEventListener('click', handler)
   
   // Later when done:
   element.removeEventListener('click', handler)
   
   // For IPC:
   const cleanup = window.electronAPI.onMessage(handler)
   // Later:
   cleanup()
   ```

### Slow Startup Time

**Problem:** Application takes too long to start.

**Possible Causes:**
1. Large dependencies being loaded at startup
2. Too many synchronous operations
3. Inefficient resource loading

**Solutions:**

1. **Measure startup performance:**
   ```javascript
   // In main.js
   const startTime = Date.now()
   
   app.whenReady().then(() => {
     console.log(`App ready time: ${Date.now() - startTime}ms`)
   })
   
   // In renderer
   window.addEventListener('DOMContentLoaded', () => {
     console.log(`DOM loaded time: ${Date.now() - window.performance.timing.navigationStart}ms`)
   })
   ```

2. **Lazy load components:**
   ```javascript
   // Only load what's needed for startup
   // Lazy load the rest
   
   // Example with dynamic imports
   document.getElementById('feature-button').addEventListener('click', async () => {
     const { initFeature } = await import('./heavy-feature.js')
     initFeature()
   })
   ```

3. **Use background initialization:**
   ```javascript
   // Show UI immediately, then initialize features
   app.whenReady().then(() => {
     createWindow()
     mainWindow.once('ready-to-show', () => {
       mainWindow.show()
       
       // Initialize non-critical features in background
       setTimeout(() => {
         initBackgroundFeatures()
       }, 1000)
     })
   })
   ```

## Packaging and Distribution

### Missing Dependencies in Packaged App

**Problem:** App works in development but crashes when packaged.

**Possible Causes:**
1. Dependencies not included in the package
2. Native module compatibility issues
3. Path resolution differences

**Solutions:**

1. **Include all dependencies:**
   ```json
   // In package.json
   {
     "build": {
       "files": [
         "**/*",
         "!node_modules/*/{CHANGELOG.md,README.md,README,readme.md,readme}",
         "!node_modules/*/{test,__tests__,tests,powered-test,example,examples}",
         "!node_modules/.bin",
         "!**/*.{iml,o,hprof,orig,pyc,pyo,rbc,swp,csproj,sln,xproj}",
         "!.editorconfig",
         "!**/._*",
         "!**/{.DS_Store,.git,.hg,.svn,CVS,RCS,SCCS,.gitignore,.gitattributes}",
         "!**/{__pycache__,thumbs.db,.flowconfig,.idea,.vs,.nyc_output}",
         "!**/{appveyor.yml,.travis.yml,circle.yml}",
         "!**/{npm-debug.log,yarn.lock,.yarn-integrity,.yarn-metadata.json}"
       ],
       "extraResources": [
         {
           "from": "resources/",
           "to": "resources/"
         }
       ]
     }
   }
   ```

2. **Rebuild native modules:**
   ```bash
   # Before packaging
   npx electron-builder install-app-deps
   ```

3. **Use proper path resolution:**
   ```javascript
   // In development
   const isDev = process.env.NODE_ENV === 'development'
   
   // Get base path for resources
   const getResourcePath = (resourcePath) => {
     if (isDev) {
       return path.join(__dirname, resourcePath)
     } else {
       return path.join(process.resourcesPath, resourcePath)
     }
   }
   
   // Use consistently
   const configPath = getResourcePath('config.json')
   ```

### Code Signing Issues

**Problem:** Application fails signature verification or shows security warnings.

**Possible Causes:**
1. Missing or invalid code signing certificate
2. Incorrect signing configuration
3. Platform-specific requirements not met

**Solutions:**

1. **Configure code signing in electron-builder:**
   ```json
   // In package.json
   {
     "build": {
       "mac": {
         "hardenedRuntime": true,
         "gatekeeperAssess": false,
         "entitlements": "build/entitlements.mac.plist",
         "entitlementsInherit": "build/entitlements.mac.plist",
         "sign": "Developer ID Application: Your Company"
       },
       "win": {
         "certificateFile": "path/to/certificate.pfx",
         "certificatePassword": "env:CERTIFICATE_PASSWORD"
       }
     }
   }
   ```

2. **Set up environment variables securely:**
   ```bash
   # For CI/CD systems, set secrets securely
   # For local builds:
   export CSC_LINK=path/to/certificate
   export CSC_KEY_PASSWORD=your-password
   ```

3. **Verify signatures after build:**
   ```bash
   # macOS
   codesign -dv --verbose=4 /path/to/YourApp.app
   
   # Windows
   signtool verify /pa /v your-app.exe
   ```

## Debugging Tips

1. **Enable logging:**
   ```javascript
   // In main.js
   app.commandLine.appendSwitch('enable-logging')
   app.commandLine.appendSwitch('log-level', '0')
   ```

2. **Use remote debugging:**
   ```javascript
   // In main.js
   app.commandLine.appendSwitch('remote-debugging-port', '9222')
   
   // Then open in Chrome:
   // chrome://inspect
   ```

3. **Create a crash reporter:**
   ```javascript
   // In main.js
   const { crashReporter } = require('electron')
   
   crashReporter.start({
     productName: 'YourApp',
     companyName: 'YourCompany',
     submitURL: 'https://your-crash-report-server.com/submit',
     uploadToServer: true
   })
   ```

4. **Save logs to file:**
   ```javascript
   // In main.js
   const fs = require('fs')
   const path = require('path')
   const logPath = path.join(app.getPath('userData'), 'logs.txt')
   
   // Redirect console to file
   const log = fs.createWriteStream(logPath, { flags: 'a' })
   const originalConsoleLog = console.log
   const originalConsoleError = console.error
   
   console.log = (...args) => {
     originalConsoleLog(...args)
     log.write(`[LOG][${new Date().toISOString()}] ${args.join(' ')}\n`)
   }
   
   console.error = (...args) => {
     originalConsoleError(...args)
     log.write(`[ERROR][${new Date().toISOString()}] ${args.join(' ')}\n`)
   }
   ```