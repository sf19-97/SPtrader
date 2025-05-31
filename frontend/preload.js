// Preload script for secure API communication
const { contextBridge, ipcRenderer } = require('electron');
const path = require('path');
const fs = require('fs');

// Expose a safe API for the renderer to communicate with the backend
contextBridge.exposeInMainWorld('api', {
  // API base URL
  baseUrl: 'http://localhost:8080',
  
  // Helper to check if API is available
  checkConnection: async () => {
    try {
      const response = await fetch('http://localhost:8080/api/v1/health');
      return response.ok;
    } catch (error) {
      return false;
    }
  },
  
  // Get the forex session filter code
  getForexSessionFilter: () => {
    try {
      const filterPath = path.join(__dirname, 'src/utils/forex_session_filter.js');
      return fs.readFileSync(filterPath, 'utf8');
    } catch (error) {
      console.error('Error loading forex session filter:', error);
      return null;
    }
  }
});