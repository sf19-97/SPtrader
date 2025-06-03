/**
 * Example of Vue.js Integration with Electron
 * 
 * This example demonstrates:
 * - Setting up Vue.js in an Electron app
 * - Using IPC communication between Vue and main process
 * - State management with Vuex in Electron context
 * - File system access from Vue via Electron API
 */

// === MAIN PROCESS (main.js) ===

const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const fs = require('fs')

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  // In development, you might load from Vue dev server
  const isDev = process.env.NODE_ENV === 'development'
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:8080')
    mainWindow.webContents.openDevTools()
  } else {
    // In production, load the built Vue app
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(() => {
  createWindow()

  // Re-create window on macOS when dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC handlers for Vue frontend
ipcMain.handle('dialog:openFile', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: 'Text Files', extensions: ['txt', 'md'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  
  if (canceled) {
    return null
  }
  
  const filePath = filePaths[0]
  const content = fs.readFileSync(filePath, 'utf8')
  
  return {
    filePath,
    content
  }
})

ipcMain.handle('dialog:saveFile', async (event, content) => {
  const { canceled, filePath } = await dialog.showSaveDialog({
    filters: [
      { name: 'Text Files', extensions: ['txt'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  
  if (!canceled && filePath) {
    fs.writeFileSync(filePath, content, 'utf8')
    return { success: true, filePath }
  }
  
  return { success: false }
})

ipcMain.handle('app:getInfo', () => {
  return {
    appName: app.getName(),
    appVersion: app.getVersion(),
    electronVersion: process.versions.electron,
    nodeVersion: process.versions.node,
    platform: process.platform,
    isDevelopment: process.env.NODE_ENV === 'development'
  }
})

// === PRELOAD SCRIPT (preload.js) ===

const { contextBridge, ipcRenderer } = require('electron')

// Expose protected API to renderer
contextBridge.exposeInMainWorld('electron', {
  // App info
  getAppInfo: () => ipcRenderer.invoke('app:getInfo'),
  
  // File operations
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (content) => ipcRenderer.invoke('dialog:saveFile', content),
  
  // Listen for events from main process
  onUpdateAvailable: (callback) => {
    const subscription = (event, ...args) => callback(...args)
    ipcRenderer.on('update-available', subscription)
    return () => {
      ipcRenderer.removeListener('update-available', subscription)
    }
  }
})

// === VUE COMPONENTS ===

// Example App.vue
/*
<template>
  <div id="app">
    <header class="app-header">
      <h1>Electron Vue Example</h1>
      <app-info v-if="appInfo" :info="appInfo" />
    </header>
    <main>
      <text-editor />
    </main>
  </div>
</template>

<script>
import AppInfo from './components/AppInfo.vue'
import TextEditor from './components/TextEditor.vue'

export default {
  name: 'App',
  components: {
    AppInfo,
    TextEditor
  },
  data() {
    return {
      appInfo: null
    }
  },
  async created() {
    // Get app info when component is created
    if (window.electron) {
      this.appInfo = await window.electron.getAppInfo()
    }
  }
}
</script>

<style>
.app-header {
  background-color: #34495e;
  color: white;
  padding: 1rem;
  text-align: center;
}

main {
  padding: 1rem;
}
</style>
*/

// Example TextEditor.vue component
/*
<template>
  <div class="text-editor">
    <div class="editor-toolbar">
      <button @click="handleOpenFile">Open File</button>
      <button @click="handleSaveFile">Save File</button>
      <span class="file-path">{{ filePath || 'No file open' }}</span>
      <span :class="['save-status', isSaved ? 'saved' : 'unsaved']">
        {{ isSaved ? 'Saved' : 'Unsaved' }}
      </span>
    </div>
    <textarea
      v-model="text"
      placeholder="Type something..."
      rows="20"
      @input="handleTextChange"
    ></textarea>
  </div>
</template>

<script>
export default {
  name: 'TextEditor',
  data() {
    return {
      text: '',
      filePath: null,
      isSaved: true
    }
  },
  methods: {
    handleTextChange() {
      this.isSaved = false
    },
    async handleOpenFile() {
      if (!this.isSaved && !confirm('You have unsaved changes. Continue?')) {
        return
      }
      
      try {
        const result = await window.electron.openFile()
        if (result) {
          this.text = result.content
          this.filePath = result.filePath
          this.isSaved = true
        }
      } catch (error) {
        console.error('Failed to open file:', error)
      }
    },
    async handleSaveFile() {
      try {
        const result = await window.electron.saveFile(this.text)
        if (result.success) {
          this.filePath = result.filePath
          this.isSaved = true
          alert('File saved successfully!')
        }
      } catch (error) {
        console.error('Failed to save file:', error)
      }
    }
  }
}
</script>

<style scoped>
.text-editor {
  border: 1px solid #ccc;
  border-radius: 4px;
  overflow: hidden;
}

.editor-toolbar {
  background-color: #f5f5f5;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

button {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #2980b9;
}

.file-path {
  flex-grow: 1;
  font-size: 0.9rem;
  color: #666;
  margin-left: 0.5rem;
}

.save-status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.saved {
  background-color: #2ecc71;
  color: white;
}

.unsaved {
  background-color: #e74c3c;
  color: white;
}

textarea {
  width: 100%;
  padding: 0.5rem;
  border: none;
  resize: vertical;
  font-family: monospace;
}

textarea:focus {
  outline: none;
}
</style>
*/

// Example AppInfo.vue component
/*
<template>
  <div class="app-info">
    <h3>App Information</h3>
    <table>
      <tbody>
        <tr>
          <td>App Name:</td>
          <td>{{ info.appName }}</td>
        </tr>
        <tr>
          <td>Version:</td>
          <td>{{ info.appVersion }}</td>
        </tr>
        <tr>
          <td>Electron:</td>
          <td>{{ info.electronVersion }}</td>
        </tr>
        <tr>
          <td>Node.js:</td>
          <td>{{ info.nodeVersion }}</td>
        </tr>
        <tr>
          <td>Platform:</td>
          <td>{{ info.platform }}</td>
        </tr>
        <tr>
          <td>Mode:</td>
          <td>{{ info.isDevelopment ? 'Development' : 'Production' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'AppInfo',
  props: {
    info: {
      type: Object,
      required: true
    }
  }
}
</script>

<style scoped>
.app-info {
  background-color: #2c3e50;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

h3 {
  margin-top: 0;
  color: #ecf0f1;
}

table {
  width: 100%;
  border-collapse: collapse;
}

td {
  padding: 0.25rem;
  color: #ecf0f1;
}

td:first-child {
  font-weight: bold;
  color: #3498db;
}
</style>
*/

// === MAIN.JS (Vue Entry Point) ===

/*
import Vue from 'vue'
import App from './App.vue'
import store from './store'

Vue.config.productionTip = false

new Vue({
  store,
  render: h => h(App)
}).$mount('#app')
*/

// === PACKAGE.JSON CONFIGURATION ===

/*
{
  "name": "electron-vue-example",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "serve": "vue-cli-service serve",
    "build": "vue-cli-service build",
    "lint": "vue-cli-service lint",
    "electron:serve": "vue-cli-service electron:serve",
    "electron:build": "vue-cli-service electron:build",
    "postinstall": "electron-builder install-app-deps",
    "postuninstall": "electron-builder install-app-deps"
  },
  "main": "background.js",
  "dependencies": {
    "core-js": "^3.8.3",
    "vue": "^2.6.14",
    "vuex": "^3.6.2"
  },
  "devDependencies": {
    "@babel/core": "^7.12.16",
    "@babel/eslint-parser": "^7.12.16",
    "@vue/cli-plugin-babel": "~5.0.0",
    "@vue/cli-plugin-eslint": "~5.0.0",
    "@vue/cli-plugin-vuex": "~5.0.0",
    "@vue/cli-service": "~5.0.0",
    "electron": "^13.0.0",
    "electron-devtools-installer": "^3.1.0",
    "vue-cli-plugin-electron-builder": "~2.1.1",
    "vue-template-compiler": "^2.6.14"
  },
  "eslintConfig": {
    "root": true,
    "env": {
      "node": true
    },
    "extends": [
      "plugin:vue/essential",
      "eslint:recommended"
    ],
    "parserOptions": {
      "parser": "@babel/eslint-parser"
    },
    "rules": {}
  },
  "browserslist": [
    "> 1%",
    "last 2 versions",
    "not dead"
  ]
}
*/

// === PROJECT STRUCTURE ===

/*
electron-vue-example/
├── public/
│   ├── index.html       # HTML template
│   └── favicon.ico
├── src/
│   ├── assets/          # Static assets
│   ├── components/
│   │   ├── AppInfo.vue    # App info component
│   │   └── TextEditor.vue # Text editor component
│   ├── store/
│   │   ├── index.js       # Vuex store
│   │   └── modules/
│   │       └── files.js   # Files module
│   ├── App.vue          # Main Vue component
│   ├── main.js          # Vue entry point
│   └── background.js    # Electron main process
├── vue.config.js        # Vue CLI configuration
└── package.json
*/

// === USING VUEX WITH ELECTRON ===

// Example store/index.js
/*
import Vue from 'vue'
import Vuex from 'vuex'
import files from './modules/files'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    files
  }
})
*/

// Example store/modules/files.js
/*
export default {
  namespaced: true,
  
  state: {
    currentFile: null,
    content: '',
    isSaved: true,
    isLoading: false,
    error: null
  },
  
  mutations: {
    SET_CURRENT_FILE(state, filePath) {
      state.currentFile = filePath
    },
    SET_CONTENT(state, content) {
      state.content = content
    },
    SET_SAVED(state, isSaved) {
      state.isSaved = isSaved
    },
    SET_LOADING(state, isLoading) {
      state.isLoading = isLoading
    },
    SET_ERROR(state, error) {
      state.error = error
    }
  },
  
  actions: {
    updateContent({ commit }, content) {
      commit('SET_CONTENT', content)
      commit('SET_SAVED', false)
    },
    
    async openFile({ commit }) {
      commit('SET_LOADING', true)
      
      try {
        if (!window.electron) {
          throw new Error('Electron API not available')
        }
        
        const result = await window.electron.openFile()
        
        if (result) {
          commit('SET_CURRENT_FILE', result.filePath)
          commit('SET_CONTENT', result.content)
          commit('SET_SAVED', true)
        }
        
        commit('SET_ERROR', null)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Failed to open file:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async saveFile({ commit, state }) {
      commit('SET_LOADING', true)
      
      try {
        if (!window.electron) {
          throw new Error('Electron API not available')
        }
        
        const result = await window.electron.saveFile(state.content)
        
        if (result.success) {
          commit('SET_CURRENT_FILE', result.filePath)
          commit('SET_SAVED', true)
        }
        
        commit('SET_ERROR', null)
        return result
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Failed to save file:', error)
        return { success: false, error: error.message }
      } finally {
        commit('SET_LOADING', false)
      }
    }
  },
  
  getters: {
    fileName(state) {
      if (!state.currentFile) return null
      return state.currentFile.split(/[\\/]/).pop()
    }
  }
}
*/

// === UPDATED TEXT EDITOR COMPONENT WITH VUEX ===

/*
<template>
  <div class="text-editor">
    <div class="editor-toolbar">
      <button @click="openFile" :disabled="isLoading">Open File</button>
      <button @click="saveFile" :disabled="isLoading">Save File</button>
      <span class="file-path">{{ currentFileName || 'No file open' }}</span>
      <span :class="['save-status', isSaved ? 'saved' : 'unsaved']">
        {{ isSaved ? 'Saved' : 'Unsaved' }}
      </span>
      <span v-if="isLoading" class="loading">Loading...</span>
    </div>
    <textarea
      v-model="textContent"
      placeholder="Type something..."
      rows="20"
      :disabled="isLoading"
    ></textarea>
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'

export default {
  name: 'TextEditor',
  
  computed: {
    ...mapState('files', [
      'content',
      'isSaved',
      'isLoading',
      'error'
    ]),
    ...mapGetters('files', ['fileName']),
    
    textContent: {
      get() {
        return this.content
      },
      set(value) {
        this.updateContent(value)
      }
    },
    
    currentFileName() {
      return this.fileName
    }
  },
  
  methods: {
    ...mapActions('files', [
      'updateContent',
      'openFile',
      'saveFile'
    ]),
    
    async handleSaveFile() {
      const result = await this.saveFile()
      if (result.success) {
        this.$notify({
          type: 'success',
          text: 'File saved successfully!'
        })
      }
    }
  }
}
</script>

<style scoped>
/* Same styles as before */
.error-message {
  color: red;
  padding: 0.5rem;
  background-color: #ffebee;
  border: 1px solid #ffcdd2;
  margin-top: 0.5rem;
  border-radius: 4px;
}

.loading {
  font-style: italic;
  color: #666;
  margin-left: 0.5rem;
}
</style>
*/

// === VUE COMPOSITION API VERSION (Vue 3) ===

/*
<template>
  <div class="text-editor">
    <div class="editor-toolbar">
      <button @click="openFile" :disabled="isLoading">Open File</button>
      <button @click="saveFile" :disabled="isLoading">Save File</button>
      <span class="file-path">{{ currentFile ? currentFile.split('/').pop() : 'No file open' }}</span>
      <span :class="['save-status', isSaved ? 'saved' : 'unsaved']">
        {{ isSaved ? 'Saved' : 'Unsaved' }}
      </span>
    </div>
    <textarea
      v-model="text"
      placeholder="Type something..."
      rows="20"
      @input="handleTextChange"
    ></textarea>
  </div>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'TextEditor',
  setup() {
    const text = ref('')
    const currentFile = ref(null)
    const isSaved = ref(true)
    const isLoading = ref(false)
    
    const handleTextChange = () => {
      isSaved.value = false
    }
    
    const openFile = async () => {
      if (!isSaved.value && !confirm('You have unsaved changes. Continue?')) {
        return
      }
      
      isLoading.value = true
      
      try {
        const result = await window.electron.openFile()
        if (result) {
          text.value = result.content
          currentFile.value = result.filePath
          isSaved.value = true
        }
      } catch (error) {
        console.error('Failed to open file:', error)
      } finally {
        isLoading.value = false
      }
    }
    
    const saveFile = async () => {
      isLoading.value = true
      
      try {
        const result = await window.electron.saveFile(text.value)
        if (result.success) {
          currentFile.value = result.filePath
          isSaved.value = true
          alert('File saved successfully!')
        }
      } catch (error) {
        console.error('Failed to save file:', error)
      } finally {
        isLoading.value = false
      }
    }
    
    // Confirm before closing if unsaved changes
    window.addEventListener('beforeunload', (e) => {
      if (!isSaved.value) {
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?'
      }
    })
    
    return {
      text,
      currentFile,
      isSaved,
      isLoading,
      handleTextChange,
      openFile,
      saveFile
    }
  }
}
</script>
*/

// === VUE ROUTER INTEGRATION ===

/*
// router/index.js
import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import Editor from '../views/Editor.vue'
import Settings from '../views/Settings.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/editor',
    name: 'Editor',
    component: Editor
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

// Use hash mode for Electron
const router = new VueRouter({
  mode: 'hash',
  base: process.env.BASE_URL,
  routes
})

export default router

// main.js
import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

Vue.config.productionTip = false

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')

// App.vue with navigation
<template>
  <div id="app">
    <nav class="app-nav">
      <router-link to="/">Home</router-link> |
      <router-link to="/editor">Editor</router-link> |
      <router-link to="/settings">Settings</router-link>
    </nav>
    <router-view/>
  </div>
</template>
*/

// === BACKGROUND.JS (Vue CLI Plugin Electron Builder) ===

/*
import { app, protocol, BrowserWindow, ipcMain, dialog } from 'electron'
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib'
import installExtension, { VUEJS_DEVTOOLS } from 'electron-devtools-installer'
import path from 'path'
import fs from 'fs'

const isDevelopment = process.env.NODE_ENV !== 'production'

// Scheme must be registered before the app is ready
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true } }
])

let mainWindow

async function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      // Use pluginOptions.nodeIntegration, leave this alone
      // See nklayman.github.io/vue-cli-plugin-electron-builder/guide/security.html#node-integration for more info
      nodeIntegration: process.env.ELECTRON_NODE_INTEGRATION,
      contextIsolation: !process.env.ELECTRON_NODE_INTEGRATION,
      preload: path.join(__dirname, 'preload.js')
    }
  })

  if (process.env.WEBPACK_DEV_SERVER_URL) {
    // Load the url of the dev server if in development mode
    await mainWindow.loadURL(process.env.WEBPACK_DEV_SERVER_URL)
    if (!process.env.IS_TEST) mainWindow.webContents.openDevTools()
  } else {
    createProtocol('app')
    // Load the index.html when not in development
    mainWindow.loadURL('app://./index.html')
  }
}

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', async () => {
  if (isDevelopment && !process.env.IS_TEST) {
    // Install Vue Devtools
    try {
      await installExtension(VUEJS_DEVTOOLS)
    } catch (e) {
      console.error('Vue Devtools failed to install:', e.toString())
    }
  }
  createWindow()
})

// Exit cleanly on request from parent process in development mode.
if (isDevelopment) {
  if (process.platform === 'win32') {
    process.on('message', (data) => {
      if (data === 'graceful-exit') {
        app.quit()
      }
    })
  } else {
    process.on('SIGTERM', () => {
      app.quit()
    })
  }
}

// IPC handlers
ipcMain.handle('dialog:openFile', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: 'Text Files', extensions: ['txt', 'md'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  
  if (canceled) {
    return null
  }
  
  const filePath = filePaths[0]
  const content = fs.readFileSync(filePath, 'utf8')
  
  return {
    filePath,
    content
  }
})

ipcMain.handle('dialog:saveFile', async (event, content) => {
  const { canceled, filePath } = await dialog.showSaveDialog({
    filters: [
      { name: 'Text Files', extensions: ['txt'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  
  if (!canceled && filePath) {
    fs.writeFileSync(filePath, content, 'utf8')
    return { success: true, filePath }
  }
  
  return { success: false }
})

ipcMain.handle('app:getInfo', () => {
  return {
    appName: app.getName(),
    appVersion: app.getVersion(),
    electronVersion: process.versions.electron,
    nodeVersion: process.versions.node,
    platform: process.platform,
    isDevelopment: process.env.NODE_ENV === 'development'
  }
})
*/