/**
 * Example Electron Preload Script
 * 
 * This example demonstrates a well-structured preload script with:
 * - Context isolation
 * - Secure IPC communication
 * - Validation of inputs and outputs
 * - Type-safe exposed APIs
 */

const { contextBridge, ipcRenderer } = require('electron')

/**
 * Safely expose IPC functionality to the renderer process
 * using contextBridge
 */

// Define valid channels for security
const validChannels = {
  // Channels the renderer can send to
  send: [
    'log-message',
    'window-minimize',
    'window-maximize',
    'window-close',
  ],
  // Channels the renderer can listen to
  receive: [
    'file-opened',
    'menu-save-triggered',
    'update-available',
    'deep-link',
  ],
  // Channels for invoke/handle pattern (request/response)
  invoke: [
    'get-app-info',
    'save-file',
    'show-dialog',
  ]
}

/**
 * Validate that a channel name is in our allowed list
 * @param {string} channel - The channel name to check
 * @param {string} type - The type of channel ('send', 'receive', or 'invoke')
 * @returns {boolean} - Whether the channel is valid
 */
function isValidChannel(channel, type) {
  if (!channel || typeof channel !== 'string') {
    return false
  }
  
  return validChannels[type]?.includes(channel) ?? false
}

/**
 * Validate message data for specific channels
 * @param {string} channel - The channel name
 * @param {any} data - The data to validate
 * @returns {boolean} - Whether the data is valid for the channel
 */
function isValidData(channel, data) {
  switch (channel) {
    case 'save-file':
      // Validate save-file data structure
      if (!data || typeof data !== 'object') return false
      if (typeof data.content !== 'string') return false
      if (data.filePath !== undefined && typeof data.filePath !== 'string') return false
      return true
    
    case 'show-dialog':
      // Validate dialog options
      if (!data || typeof data !== 'object') return false
      if (data.type && !['info', 'error', 'question', 'warning', 'none'].includes(data.type)) return false
      if (data.buttons && (!Array.isArray(data.buttons) || data.buttons.some(b => typeof b !== 'string'))) return false
      return true
    
    // Add validation for other channels as needed
    
    default:
      // For channels without specific validation, accept any data
      return true
  }
}

// App API - Application-level functionality
const appAPI = {
  /**
   * Get application information
   * @returns {Promise<Object>} App information
   */
  getInfo: async () => {
    return await ipcRenderer.invoke('get-app-info')
  },
  
  /**
   * Log a message to the main process console
   * @param {string} message - The message to log
   */
  log: (message) => {
    if (typeof message === 'string') {
      ipcRenderer.send('log-message', message)
    } else {
      console.warn('Invalid log message format, must be string')
    }
  }
}

// Window API - Window management functionality
const windowAPI = {
  /**
   * Minimize the current window
   */
  minimize: () => {
    ipcRenderer.send('window-minimize')
  },
  
  /**
   * Maximize or restore the current window
   */
  maximize: () => {
    ipcRenderer.send('window-maximize')
  },
  
  /**
   * Close the current window
   */
  close: () => {
    ipcRenderer.send('window-close')
  }
}

// File API - File operations
const fileAPI = {
  /**
   * Save content to a file
   * @param {string} content - The content to save
   * @param {string} [filePath] - Optional file path (if omitted, will show save dialog)
   * @returns {Promise<Object>} Result of the save operation
   */
  save: async (content, filePath = undefined) => {
    // Validate content
    if (typeof content !== 'string') {
      throw new Error('Content must be a string')
    }
    
    // Validate filePath if provided
    if (filePath !== undefined && typeof filePath !== 'string') {
      throw new Error('File path must be a string')
    }
    
    // Send to main process
    return await ipcRenderer.invoke('save-file', { content, filePath })
  },
  
  /**
   * Set up a listener for when files are opened
   * @param {Function} callback - Function to call when a file is opened
   * @returns {Function} Function to remove the listener
   */
  onFileOpened: (callback) => {
    if (typeof callback !== 'function') {
      throw new Error('Callback must be a function')
    }
    
    // Wrap the callback to ensure it receives exactly what we expect
    const wrappedCallback = (event, fileData) => {
      callback({
        path: fileData.path,
        content: fileData.content
      })
    }
    
    // Add listener
    ipcRenderer.on('file-opened', wrappedCallback)
    
    // Return function to remove listener
    return () => {
      ipcRenderer.removeListener('file-opened', wrappedCallback)
    }
  },
  
  /**
   * Set up a listener for when the save menu item is triggered
   * @param {Function} callback - Function to call when save is triggered
   * @returns {Function} Function to remove the listener
   */
  onSaveTriggered: (callback) => {
    if (typeof callback !== 'function') {
      throw new Error('Callback must be a function')
    }
    
    const wrappedCallback = (event) => {
      callback()
    }
    
    ipcRenderer.on('menu-save-triggered', wrappedCallback)
    
    return () => {
      ipcRenderer.removeListener('menu-save-triggered', wrappedCallback)
    }
  }
}

// Dialog API - System dialogs
const dialogAPI = {
  /**
   * Show a message dialog
   * @param {Object} options - Dialog options
   * @param {string} [options.type='info'] - Dialog type ('info', 'error', 'question', 'warning', 'none')
   * @param {string} [options.title='Message'] - Dialog title
   * @param {string} options.message - Main message text
   * @param {string} [options.detail] - Additional details
   * @param {string[]} [options.buttons=['OK']] - Button labels
   * @returns {Promise<Object>} Dialog result
   */
  show: async (options) => {
    // Validate options
    if (!options || typeof options !== 'object') {
      throw new Error('Dialog options must be an object')
    }
    
    if (!options.message || typeof options.message !== 'string') {
      throw new Error('Dialog message is required and must be a string')
    }
    
    if (options.type && !['info', 'error', 'question', 'warning', 'none'].includes(options.type)) {
      throw new Error('Invalid dialog type')
    }
    
    if (options.buttons && (!Array.isArray(options.buttons) || 
                           options.buttons.some(b => typeof b !== 'string'))) {
      throw new Error('Dialog buttons must be an array of strings')
    }
    
    // Send to main process
    return await ipcRenderer.invoke('show-dialog', options)
  }
}

// Updates API - Application updates
const updatesAPI = {
  /**
   * Set up a listener for available updates
   * @param {Function} callback - Function to call when an update is available
   * @returns {Function} Function to remove the listener
   */
  onUpdateAvailable: (callback) => {
    if (typeof callback !== 'function') {
      throw new Error('Callback must be a function')
    }
    
    const wrappedCallback = (event, updateInfo) => {
      callback({
        version: updateInfo.version,
        releaseDate: updateInfo.releaseDate,
        releaseNotes: updateInfo.releaseNotes
      })
    }
    
    ipcRenderer.on('update-available', wrappedCallback)
    
    return () => {
      ipcRenderer.removeListener('update-available', wrappedCallback)
    }
  }
}

// Deep linking API
const deepLinkAPI = {
  /**
   * Set up a listener for deep link events
   * @param {Function} callback - Function to call when a deep link is activated
   * @returns {Function} Function to remove the listener
   */
  onDeepLink: (callback) => {
    if (typeof callback !== 'function') {
      throw new Error('Callback must be a function')
    }
    
    const wrappedCallback = (event, url) => {
      callback(url)
    }
    
    ipcRenderer.on('deep-link', wrappedCallback)
    
    return () => {
      ipcRenderer.removeListener('deep-link', wrappedCallback)
    }
  }
}

// Generic communication API
const communicationAPI = {
  /**
   * Send a message to the main process on a specific channel
   * @param {string} channel - The channel to send on
   * @param {any} data - The data to send
   */
  send: (channel, data) => {
    // Validate channel
    if (!isValidChannel(channel, 'send')) {
      throw new Error(`Invalid send channel: ${channel}`)
    }
    
    // Validate data for specific channels
    if (!isValidData(channel, data)) {
      throw new Error(`Invalid data for channel: ${channel}`)
    }
    
    ipcRenderer.send(channel, data)
  },
  
  /**
   * Invoke a function in the main process and get a response
   * @param {string} channel - The channel to invoke
   * @param {any} data - The data to send
   * @returns {Promise<any>} The response from the main process
   */
  invoke: async (channel, data) => {
    // Validate channel
    if (!isValidChannel(channel, 'invoke')) {
      throw new Error(`Invalid invoke channel: ${channel}`)
    }
    
    // Validate data for specific channels
    if (!isValidData(channel, data)) {
      throw new Error(`Invalid data for channel: ${channel}`)
    }
    
    return await ipcRenderer.invoke(channel, data)
  },
  
  /**
   * Listen for messages from the main process on a specific channel
   * @param {string} channel - The channel to listen on
   * @param {Function} callback - Function to call when a message is received
   * @returns {Function} Function to remove the listener
   */
  on: (channel, callback) => {
    // Validate channel
    if (!isValidChannel(channel, 'receive')) {
      throw new Error(`Invalid receive channel: ${channel}`)
    }
    
    // Validate callback
    if (typeof callback !== 'function') {
      throw new Error('Callback must be a function')
    }
    
    // Wrap callback to avoid exposing event object
    const wrappedCallback = (event, ...args) => {
      callback(...args)
    }
    
    ipcRenderer.on(channel, wrappedCallback)
    
    // Return function to remove listener
    return () => {
      ipcRenderer.removeListener(channel, wrappedCallback)
    }
  }
}

// Expose the API to the renderer process
contextBridge.exposeInMainWorld('electron', {
  app: appAPI,
  window: windowAPI,
  file: fileAPI,
  dialog: dialogAPI,
  updates: updatesAPI,
  deepLink: deepLinkAPI,
  communication: communicationAPI,
  
  // System information (read-only)
  system: {
    platform: process.platform,
    arch: process.arch,
    version: process.versions.electron
  }
})