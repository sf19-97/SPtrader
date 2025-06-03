// run_test_page.js - Simple script to run a test page in Electron
const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;

// Get the file to open from command line arguments
const fileToOpen = process.argv[2] || 'index.html';
console.log(`Opening: ${fileToOpen}`);

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    title: 'SPtrader Test - ' + fileToOpen,
    webPreferences: {
      nodeIntegration: true, // Enable for test pages
      contextIsolation: false,
      webSecurity: false
    },
    backgroundColor: '#1e1e1e'
  });

  // Load the specified file
  const filePath = path.join(__dirname, '..', 'frontend', fileToOpen);
  mainWindow.loadFile(filePath);
  
  // Open DevTools
  mainWindow.webContents.openDevTools();

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});