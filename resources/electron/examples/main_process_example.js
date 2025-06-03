/**
 * Example Electron Main Process
 * 
 * This example demonstrates a well-structured main process with:
 * - Proper window management
 * - Secure IPC communication
 * - Menu configuration
 * - App lifecycle handling
 */

const { app, BrowserWindow, ipcMain, Menu, dialog, shell } = require('electron')
const path = require('path')
const fs = require('fs')

// Keep a global reference to prevent garbage collection
let mainWindow

// App configuration
const appConfig = {
  name: 'ElectronExample',
  width: 1200,
  height: 800,
  minWidth: 800,
  minHeight: 600,
  devTools: process.env.NODE_ENV === 'development'
}

/**
 * Create the main application window
 */
function createMainWindow() {
  // Create the browser window with secure defaults
  mainWindow = new BrowserWindow({
    width: appConfig.width,
    height: appConfig.height,
    minWidth: appConfig.minWidth,
    minHeight: appConfig.minHeight,
    title: appConfig.name,
    show: false, // Don't show until ready
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      enableRemoteModule: false
    }
  })

  // Load the index.html of the app
  mainWindow.loadFile(path.join(__dirname, 'index.html'))

  // Show window when ready to prevent flickering
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  // Open DevTools in development mode
  if (appConfig.devTools) {
    mainWindow.webContents.openDevTools()
  }

  // Handle window closing
  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Set up external link handling
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // Check if URL is safe to open
    if (url.startsWith('https://') && isTrustedDomain(url)) {
      shell.openExternal(url)
    } else {
      console.warn(`Blocked opening untrusted URL: ${url}`)
    }
    return { action: 'deny' }
  })

  // Create application menu
  setupApplicationMenu()
}

/**
 * Check if a URL domain is in our trusted domains list
 */
function isTrustedDomain(urlString) {
  try {
    const url = new URL(urlString)
    const trustedDomains = ['electronjs.org', 'github.com', 'example.com']
    return trustedDomains.some(domain => url.hostname === domain || 
                                        url.hostname.endsWith(`.${domain}`))
  } catch (error) {
    console.error('URL parsing error:', error)
    return false
  }
}

/**
 * Set up the application menu
 */
function setupApplicationMenu() {
  const isMac = process.platform === 'darwin'
  
  const template = [
    // App menu (macOS only)
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),
    
    // File menu
    {
      label: 'File',
      submenu: [
        {
          label: 'Open File',
          accelerator: 'CmdOrCtrl+O',
          click: () => handleOpenFile()
        },
        {
          label: 'Save',
          accelerator: 'CmdOrCtrl+S',
          click: () => {
            mainWindow.webContents.send('menu-save-triggered')
          }
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },
    
    // Edit menu
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        ...(isMac ? [
          { role: 'pasteAndMatchStyle' },
          { role: 'delete' },
          { role: 'selectAll' },
          { type: 'separator' },
          {
            label: 'Speech',
            submenu: [
              { role: 'startSpeaking' },
              { role: 'stopSpeaking' }
            ]
          }
        ] : [
          { role: 'delete' },
          { type: 'separator' },
          { role: 'selectAll' }
        ])
      ]
    },
    
    // View menu
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        ...(appConfig.devTools ? [{ role: 'toggleDevTools' }] : []),
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    
    // Window menu
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        ...(isMac ? [
          { type: 'separator' },
          { role: 'front' },
          { type: 'separator' },
          { role: 'window' }
        ] : [
          { role: 'close' }
        ])
      ]
    },
    
    // Help menu
    {
      role: 'help',
      submenu: [
        {
          label: 'Documentation',
          click: async () => {
            await shell.openExternal('https://electronjs.org/docs')
          }
        },
        {
          label: 'Report Issue',
          click: async () => {
            await shell.openExternal('https://github.com/example/repo/issues')
          }
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => showAboutDialog()
        }
      ]
    }
  ]
  
  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}

/**
 * Show the about dialog
 */
function showAboutDialog() {
  dialog.showMessageBox(mainWindow, {
    title: 'About',
    message: `${appConfig.name}`,
    detail: `Version: ${app.getVersion()}\nElectron: ${process.versions.electron}\nChrome: ${process.versions.chrome}\nNode.js: ${process.versions.node}\nV8: ${process.versions.v8}`,
    buttons: ['OK'],
    icon: path.join(__dirname, 'assets/icons/icon.png')
  })
}

/**
 * Handle opening files from the menu
 */
async function handleOpenFile() {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile'],
      filters: [
        { name: 'Text Files', extensions: ['txt', 'md'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    })
    
    if (!result.canceled && result.filePaths.length > 0) {
      const filePath = result.filePaths[0]
      
      try {
        const content = fs.readFileSync(filePath, 'utf8')
        mainWindow.webContents.send('file-opened', { path: filePath, content })
      } catch (error) {
        dialog.showErrorBox('Error Opening File', `Could not open file: ${error.message}`)
      }
    }
  } catch (error) {
    console.error('Error in open dialog:', error)
  }
}

// Set up IPC handlers
function setupIpcHandlers() {
  // Get app information
  ipcMain.handle('get-app-info', () => {
    return {
      name: app.getName(),
      version: app.getVersion(),
      electron: process.versions.electron,
      chrome: process.versions.chrome,
      node: process.versions.node,
      platform: process.platform,
      arch: process.arch
    }
  })
  
  // Save file
  ipcMain.handle('save-file', async (event, { content, filePath }) => {
    try {
      // If no path provided, show save dialog
      if (!filePath) {
        const result = await dialog.showSaveDialog(mainWindow, {
          filters: [
            { name: 'Text Files', extensions: ['txt'] },
            { name: 'All Files', extensions: ['*'] }
          ]
        })
        
        if (result.canceled) {
          return { success: false, canceled: true }
        }
        
        filePath = result.filePath
      }
      
      // Validate input
      if (typeof content !== 'string') {
        throw new Error('Content must be a string')
      }
      
      // Write the file
      fs.writeFileSync(filePath, content, 'utf8')
      
      return { success: true, path: filePath }
    } catch (error) {
      console.error('Error saving file:', error)
      return { success: false, error: error.message }
    }
  })
  
  // Show dialog
  ipcMain.handle('show-dialog', async (event, options) => {
    try {
      // Validate options
      if (!options || typeof options !== 'object') {
        throw new Error('Dialog options must be an object')
      }
      
      // Set default values
      const dialogOptions = {
        type: options.type || 'info',
        title: options.title || 'Message',
        message: options.message || '',
        detail: options.detail || '',
        buttons: Array.isArray(options.buttons) ? options.buttons : ['OK']
      }
      
      const result = await dialog.showMessageBox(mainWindow, dialogOptions)
      return result
    } catch (error) {
      console.error('Error showing dialog:', error)
      return { error: error.message }
    }
  })
}

// App lifecycle events
app.on('ready', () => {
  createMainWindow()
  setupIpcHandlers()
  
  // Set up protocol handler
  if (process.defaultApp) {
    if (process.argv.length >= 2) {
      app.setAsDefaultProtocolClient('electron-example', process.execPath, [
        path.resolve(process.argv[1])
      ])
    }
  } else {
    app.setAsDefaultProtocolClient('electron-example')
  }
})

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// On macOS, re-create window when dock icon is clicked
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow()
  }
})

// Handle protocol links (deep linking)
app.on('open-url', (event, url) => {
  event.preventDefault()
  
  // Parse and handle the URL
  const parsedUrl = new URL(url)
  console.log('Deep link received:', parsedUrl.pathname)
  
  // If app is already running, send to renderer
  if (mainWindow) {
    mainWindow.webContents.send('deep-link', url)
  } else {
    // Store for when window is created
    global.deepLinkUrl = url
  }
})

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error)
  
  // Show error dialog if window is available
  if (mainWindow) {
    dialog.showErrorBox(
      'An error occurred',
      `Uncaught exception: ${error.message}\n\nThe application will continue running, but may not work as expected.`
    )
  }
})