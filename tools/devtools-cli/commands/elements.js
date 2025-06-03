const CDP = require('chrome-remote-interface');
const fs = require('fs-extra');
const path = require('path');

async function inspect(selector = 'body') {
  console.log(`Inspecting DOM elements with selector: ${selector}`);
  let client;
  
  try {
    client = await CDP();
    const { DOM, Runtime } = client;
    
    // Enable domains
    await DOM.enable();
    await Runtime.enable();
    
    // Get document
    const { root } = await DOM.getDocument();
    
    // Find elements
    const result = await Runtime.evaluate({
      expression: `document.querySelectorAll('${selector}')`,
      returnByValue: false
    });
    
    // Get element details
    const evalResult = await Runtime.evaluate({
      expression: `
        (() => {
          const elements = document.querySelectorAll('${selector}');
          return Array.from(elements).map(el => ({
            tagName: el.tagName,
            id: el.id,
            className: el.className,
            textContent: el.textContent.substring(0, 100),
            attributes: Array.from(el.attributes).map(attr => ({
              name: attr.name,
              value: attr.value
            })),
            boundingBox: el.getBoundingClientRect().toJSON()
          }));
        })()
      `,
      returnByValue: true
    });
    
    // Save output
    const outputPath = path.join(__dirname, '../output/elements.json');
    fs.writeJsonSync(outputPath, evalResult.result.value, { spaces: 2 });
    
    console.log(`Element inspection complete. Saved to ${outputPath}`);
  } catch (error) {
    console.error('Error inspecting elements:', error);
  } finally {
    if (client) {
      await client.close();
    }
  }
}

module.exports = { inspect };