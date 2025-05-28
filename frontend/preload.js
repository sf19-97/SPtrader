// Preload script for secure API communication
const { contextBridge } = require('electron');

// Expose a safe API for the renderer to communicate with the backend
contextBridge.exposeInMainWorld('api', {
  // API base URL
  baseUrl: 'http://localhost:8080',
  
  // Helper to check if API is available
  checkConnection: async () => {
    try {
      const response = await fetch('http://localhost:8080/api/health');
      return response.ok;
    } catch (error) {
      return false;
    }
  }
});