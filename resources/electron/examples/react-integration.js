/**
 * Example of React Integration with Electron
 * 
 * This example demonstrates:
 * - Setting up React in an Electron app
 * - Using IPC communication between React and main process
 * - Managing state with React in Electron context
 * - File system access from React via Electron API
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

  // In development, you might load from React dev server
  const isDev = process.env.NODE_ENV === 'development'
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000')
    mainWindow.webContents.openDevTools()
  } else {
    // In production, load the built React app
    mainWindow.loadFile(path.join(__dirname, 'build', 'index.html'))
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

// IPC handlers for React frontend
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

// === REACT COMPONENTS ===

// Example App.js
/*
import React, { useState, useEffect } from 'react';
import './App.css';
import TextEditor from './components/TextEditor';
import AppInfo from './components/AppInfo';

function App() {
  const [appInfo, setAppInfo] = useState(null);
  
  useEffect(() => {
    // Get app info when component mounts
    async function getAppInfo() {
      if (window.electron) {
        const info = await window.electron.getAppInfo();
        setAppInfo(info);
      }
    }
    
    getAppInfo();
  }, []);
  
  return (
    <div className="App">
      <header className="App-header">
        <h1>Electron React Example</h1>
        {appInfo && <AppInfo info={appInfo} />}
      </header>
      <main>
        <TextEditor />
      </main>
    </div>
  );
}

export default App;
*/

// Example TextEditor component
/*
import React, { useState } from 'react';
import './TextEditor.css';

function TextEditor() {
  const [text, setText] = useState('');
  const [filePath, setFilePath] = useState(null);
  const [isSaved, setIsSaved] = useState(true);
  
  const handleTextChange = (e) => {
    setText(e.target.value);
    setIsSaved(false);
  };
  
  const handleOpenFile = async () => {
    if (!isSaved && window.confirm('You have unsaved changes. Continue?')) {
      return;
    }
    
    try {
      const result = await window.electron.openFile();
      if (result) {
        setText(result.content);
        setFilePath(result.filePath);
        setIsSaved(true);
      }
    } catch (error) {
      console.error('Failed to open file:', error);
    }
  };
  
  const handleSaveFile = async () => {
    try {
      const result = await window.electron.saveFile(text);
      if (result.success) {
        setFilePath(result.filePath);
        setIsSaved(true);
        alert('File saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save file:', error);
    }
  };
  
  return (
    <div className="text-editor">
      <div className="editor-toolbar">
        <button onClick={handleOpenFile}>Open File</button>
        <button onClick={handleSaveFile}>Save File</button>
        <span className="file-path">{filePath || 'No file open'}</span>
        <span className={`save-status ${isSaved ? 'saved' : 'unsaved'}`}>
          {isSaved ? 'Saved' : 'Unsaved'}
        </span>
      </div>
      <textarea
        value={text}
        onChange={handleTextChange}
        placeholder="Type something..."
        rows={20}
      />
    </div>
  );
}

export default TextEditor;
*/

// Example AppInfo component
/*
import React from 'react';
import './AppInfo.css';

function AppInfo({ info }) {
  return (
    <div className="app-info">
      <h3>App Information</h3>
      <table>
        <tbody>
          <tr>
            <td>App Name:</td>
            <td>{info.appName}</td>
          </tr>
          <tr>
            <td>Version:</td>
            <td>{info.appVersion}</td>
          </tr>
          <tr>
            <td>Electron:</td>
            <td>{info.electronVersion}</td>
          </tr>
          <tr>
            <td>Node.js:</td>
            <td>{info.nodeVersion}</td>
          </tr>
          <tr>
            <td>Platform:</td>
            <td>{info.platform}</td>
          </tr>
          <tr>
            <td>Mode:</td>
            <td>{info.isDevelopment ? 'Development' : 'Production'}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default AppInfo;
*/

// === PACKAGE.JSON CONFIGURATION ===

/*
{
  "name": "electron-react-example",
  "version": "1.0.0",
  "private": true,
  "main": "public/electron.js",
  "homepage": "./",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "devDependencies": {
    "concurrently": "^8.2.0",
    "electron": "^24.3.0",
    "electron-builder": "^23.6.0",
    "electron-is-dev": "^2.0.0",
    "wait-on": "^7.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "electron:dev": "concurrently \"npm start\" \"wait-on http://localhost:3000 && electron .\"",
    "electron:build": "npm run build && electron-builder",
    "release": "npm run build && electron-builder --publish=always"
  },
  "build": {
    "appId": "com.example.electron-react",
    "files": [
      "build/**/*",
      "node_modules/**/*",
      "public/electron.js",
      "public/preload.js"
    ],
    "directories": {
      "buildResources": "assets"
    },
    "mac": {
      "category": "public.app-category.utilities"
    },
    "win": {
      "target": ["nsis"]
    },
    "linux": {
      "target": ["AppImage", "deb"]
    }
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      "last 1 electron version"
    ],
    "development": [
      "last 1 electron version"
    ]
  }
}
*/

// === PROJECT STRUCTURE ===

/*
electron-react-example/
├── public/
│   ├── electron.js       # Main process
│   ├── preload.js        # Preload script
│   ├── index.html        # HTML template
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── AppInfo.js      # App info component
│   │   ├── AppInfo.css
│   │   ├── TextEditor.js   # Text editor component
│   │   └── TextEditor.css
│   ├── App.js            # Main React component
│   ├── App.css
│   ├── index.js          # React entry point
│   └── index.css
├── assets/               # App icons and resources
├── package.json
└── README.md
*/

// === USING REACT HOOKS WITH ELECTRON ===

// Example of a custom hook for IPC communication
/*
import { useState, useEffect } from 'react';

// Hook for invoking Electron IPC calls
export function useIpcRenderer(channel, ...args) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    const invokeIpc = async () => {
      setIsLoading(true);
      try {
        if (!window.electron) {
          throw new Error('Electron IPC not available');
        }
        
        const data = await window.electron[channel](...args);
        setResult(data);
        setError(null);
      } catch (err) {
        setError(err);
        setResult(null);
      } finally {
        setIsLoading(false);
      }
    };
    
    invokeIpc();
  }, [channel, ...args]);
  
  return { result, error, isLoading };
}

// Hook for Electron events
export function useIpcEvent(eventName, callback) {
  useEffect(() => {
    if (!window.electron) {
      console.error('Electron IPC not available');
      return;
    }
    
    // Set up event listener
    const removeListener = window.electron['on' + eventName](callback);
    
    // Clean up
    return () => {
      if (removeListener && typeof removeListener === 'function') {
        removeListener();
      }
    };
  }, [eventName, callback]);
}
*/

// === USING WITH REACT ROUTER ===

/*
import { HashRouter, Routes, Route } from 'react-router-dom';

// Use HashRouter instead of BrowserRouter for Electron
function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/editor" element={<EditorPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </HashRouter>
  );
}
*/

// === USING WITH REDUX ===

/*
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import rootReducer from './reducers';

// Create store
const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) => 
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore non-serializable values in electron-related actions
        ignoredActions: ['electron/fileOpened'],
        ignoredPaths: ['files.currentFile']
      }
    })
});

// Wrap app with Provider
ReactDOM.render(
  <Provider store={store}>
    <App />
  </Provider>,
  document.getElementById('root')
);

// Example Redux slice for file operations
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const openFile = createAsyncThunk(
  'files/openFile',
  async (_, { rejectWithValue }) => {
    try {
      return await window.electron.openFile();
    } catch (error) {
      return rejectWithValue(error.toString());
    }
  }
);

export const saveFile = createAsyncThunk(
  'files/saveFile',
  async (content, { rejectWithValue }) => {
    try {
      return await window.electron.saveFile(content);
    } catch (error) {
      return rejectWithValue(error.toString());
    }
  }
);

const filesSlice = createSlice({
  name: 'files',
  initialState: {
    currentFile: null,
    content: '',
    isSaved: true,
    isLoading: false,
    error: null
  },
  reducers: {
    updateContent: (state, action) => {
      state.content = action.payload;
      state.isSaved = false;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(openFile.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(openFile.fulfilled, (state, action) => {
        if (action.payload) {
          state.currentFile = action.payload.filePath;
          state.content = action.payload.content;
          state.isSaved = true;
        }
        state.isLoading = false;
        state.error = null;
      })
      .addCase(openFile.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      })
      .addCase(saveFile.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(saveFile.fulfilled, (state, action) => {
        if (action.payload.success) {
          state.currentFile = action.payload.filePath;
          state.isSaved = true;
        }
        state.isLoading = false;
        state.error = null;
      })
      .addCase(saveFile.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });
  }
});

export const { updateContent } = filesSlice.actions;
export default filesSlice.reducer;
*/

// === HANDLING NATIVE FEATURES ===

/*
// Menu integration with React
import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { openFile, saveFile } from '../redux/filesSlice';

function useNativeMenuIntegration() {
  const dispatch = useDispatch();
  
  useEffect(() => {
    // Set up IPC listeners for menu actions
    const removeOpenListener = window.electron.onMenuOpenFile(() => {
      dispatch(openFile());
    });
    
    const removeSaveListener = window.electron.onMenuSaveFile(() => {
      dispatch(saveFile());
    });
    
    // Clean up listeners
    return () => {
      removeOpenListener();
      removeSaveListener();
    };
  }, [dispatch]);
}

// Usage in a component
function App() {
  useNativeMenuIntegration();
  
  // Rest of component...
}
*/