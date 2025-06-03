const CDP = require('chrome-remote-interface');
const fs = require('fs-extra');
const path = require('path');

async function capture() {
  console.log('Capturing network requests...');
  let client;
  
  try {
    // Connect to Chrome DevTools Protocol
    client = await CDP();
    const { Network, Page } = client;
    
    // Setup Network events
    await Network.enable();
    
    // Store captured requests
    const requests = [];
    
    Network.requestWillBeSent((params) => {
      requests.push({
        requestId: params.requestId,
        url: params.request.url,
        method: params.request.method,
        timestamp: new Date().toISOString(),
        type: params.type
      });
    });
    
    // Capture for 5 seconds
    console.log('Monitoring network activity for 5 seconds...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Save output
    const outputPath = path.join(__dirname, '../output/network-requests.json');
    fs.writeJsonSync(outputPath, requests, { spaces: 2 });
    
    console.log(`Captured ${requests.length} network requests. Saved to ${outputPath}`);
  } catch (error) {
    console.error('Error capturing network requests:', error);
  } finally {
    if (client) {
      await client.close();
    }
  }
}

module.exports = { capture };