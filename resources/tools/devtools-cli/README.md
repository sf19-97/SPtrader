# SPtrader DevTools CLI

*Created: May 31, 2025*

A command-line interface for interacting with the Electron DevTools of the SPtrader application. This tool enables programmatic access to DevTools functionality including network monitoring, DOM inspection, console logging, performance analysis, and application state inspection.

## Overview

The DevTools CLI provides a bridge between command-line operations and the Chrome DevTools Protocol (CDP), allowing you to automate DevTools interactions and extract information from the running SPtrader Electron application.

## Installation

The tool is pre-installed in the SPtrader repository. All dependencies are isolated within the `tools/devtools-cli` directory and do not affect other parts of the codebase.

### Setup

Run the setup script to configure the CLI for your environment:

```bash
cd /home/millet_frazier/SPtrader/tools/devtools-cli
./setup.sh
```

This will install dependencies and run an interactive configuration wizard.

### Dependencies

- Node.js (built with Node.js v18+)
- npm packages (locally installed):
  - chrome-remote-interface
  - minimist
  - fs-extra
  - winston
  - @inquirer/prompts

## Usage

```bash
./devtools-cli.sh <command> [options]
```

Or use the full path:

```bash
/home/millet_frazier/SPtrader/tools/devtools-cli/devtools-cli.sh <command> [options]
```

### Available Commands

| Command | Description | Options |
|---------|-------------|---------|
| `network` | Captures network requests | None |
| `elements` | Inspects DOM elements | Optional: CSS selector (default: 'body') |
| `console` | Retrieves console logs | None |
| `performance` | Measures performance metrics | None |
| `state` | Dumps application state | None |
| `help` | Shows help information | None |

### Output Format

By default, all commands output JSON files to the `output/` directory. You can optionally specify a text format:

```bash
./devtools-cli.sh <command> text
```

This will convert the JSON output to formatted text when displaying results.

## Command Details

### Network Monitoring

Captures network requests made by the Electron application.

```bash
./devtools-cli.sh network
```

**Output**: `output/network-requests.json`

Sample output:
```json
[
  {
    "requestId": "1000.100",
    "url": "http://localhost:8080/api/v1/health",
    "method": "GET",
    "timestamp": "2025-05-31T14:50:23.456Z",
    "type": "xhr"
  },
  ...
]
```

### DOM Element Inspection

Inspects DOM elements matching a specified selector.

```bash
./devtools-cli.sh elements "#chart"
```

**Output**: `output/elements.json`

Sample output:
```json
[
  {
    "tagName": "DIV",
    "id": "chart",
    "className": "chart-container",
    "textContent": "",
    "attributes": [
      {
        "name": "id",
        "value": "chart"
      },
      {
        "name": "class",
        "value": "chart-container"
      }
    ],
    "boundingBox": {
      "x": 0,
      "y": 60,
      "width": 1280,
      "height": 740,
      "top": 60,
      "right": 1280,
      "bottom": 800,
      "left": 0
    }
  }
]
```

### Console Logs

Retrieves console logs from the application and sets up logging capture for future logs.

```bash
./devtools-cli.sh console
```

**Output**: `output/console-logs.json`

Sample output:
```json
[
  {
    "type": "log",
    "timestamp": "2025-05-31T14:52:10.123Z",
    "args": ["Viewport: 2024-01-01T00:00:00.000Z to 2024-01-02T00:00:00.000Z"]
  },
  {
    "type": "error",
    "timestamp": "2025-05-31T14:52:11.234Z",
    "args": ["Failed to load data: Network error"]
  }
]
```

### Performance Analysis

Measures various performance metrics of the application.

```bash
./devtools-cli.sh performance
```

**Output**: `output/performance.json`

Sample output:
```json
{
  "metrics": [
    {
      "name": "Timestamp",
      "value": 123456789.123
    },
    {
      "name": "TaskDuration",
      "value": 0.321
    },
    ...
  ],
  "memory": {
    "totalJSHeapSize": 24000000,
    "usedJSHeapSize": 18000000,
    "jsHeapSizeLimit": 2330000000
  },
  "timing": {
    "connectStart": 1590000000123,
    "domComplete": 1590000002345,
    ...
  },
  "timestamp": "2025-05-31T14:55:00.000Z"
}
```

### Application State

Dumps the current state of the application including chart data, component status, and UI state.

```bash
./devtools-cli.sh state
```

**Output**: `output/app-state.json`

Sample output:
```json
{
  "chart": {
    "exists": true,
    "timeScale": true
  },
  "candleSeries": true,
  "virtualDataManager": {
    "exists": true,
    "windowSize": 2000000
  },
  "forexSessionFilter": true,
  "smartScaling": true,
  "candleData": {
    "length": 1500,
    "sampleData": [
      {
        "time": 1609459200,
        "open": 1.2250,
        "high": 1.2255,
        "low": 1.2245,
        "close": 1.2252
      },
      {
        "time": 1609459260,
        "open": 1.2252,
        "high": 1.2258,
        "low": 1.2251,
        "close": 1.2256
      }
    ]
  },
  "symbol": "EURUSD",
  "timeframe": "1h",
  "windowDimensions": {
    "width": 1280,
    "height": 800
  }
}
```

## Integration with Claude Code

This tool is designed to be easily used by Claude Code. Example of how Claude Code can use this tool:

```bash
# Check application state
/home/millet_frazier/SPtrader/tools/devtools-cli/devtools-cli.sh state

# Read the output
cat /home/millet_frazier/SPtrader/tools/devtools-cli/output/app-state.json
```

## Extending the Tool

### Adding a New Command

1. Create a new file in the `commands/` directory (e.g., `commands/newcommand.js`)
2. Implement the command logic using Chrome DevTools Protocol
3. Export the main function
4. Add the command to the switch statement in `devtools.js`
5. Update the help text in `devtools.js` and `devtools-cli.sh`

Example command structure:

```javascript
const CDP = require('chrome-remote-interface');
const fs = require('fs-extra');
const path = require('path');

async function myNewCommand(param) {
  console.log('Executing new command...');
  let client;
  
  try {
    client = await CDP();
    const { Runtime } = client;
    
    // Execute CDP operations
    const result = await Runtime.evaluate({
      expression: 'window.myValue',
      returnByValue: true
    });
    
    // Save output
    const outputPath = path.join(__dirname, '../output/new-command.json');
    fs.writeJsonSync(outputPath, result.result.value, { spaces: 2 });
    
    console.log(`Command completed. Saved to ${outputPath}`);
  } catch (error) {
    console.error('Error executing command:', error);
  } finally {
    if (client) {
      await client.close();
    }
  }
}

module.exports = { myNewCommand };
```

## Troubleshooting

### Cannot Connect to DevTools

- Ensure the Electron app is running
- Check if the DevTools port is accessible (default is 9222)
- Verify there are no firewalls blocking the connection

### No Output Generated

- Check if the output directory exists and is writable
- Look for error messages in the terminal
- Examine the log file: `devtools-cli.log`

### Command Hangs

- Set timeout values in CDP calls
- Check if the Electron app is responsive
- Kill the process and try again

## Technical Details

### Chrome DevTools Protocol

This tool uses the Chrome DevTools Protocol (CDP) to communicate with the Electron renderer process. CDP provides programmatic access to browser features including:

- Network monitoring
- DOM inspection
- JavaScript execution
- Performance metrics
- Console integration

### Security Considerations

- The tool runs with the same permissions as the user executing it
- It only connects to locally running Electron processes
- No permanent modifications are made to the Electron app

## References

- [Chrome DevTools Protocol Documentation](https://chromedevtools.github.io/devtools-protocol/)
- [chrome-remote-interface Package](https://github.com/cyrus-and/chrome-remote-interface)
- [Electron DevTools Documentation](https://www.electronjs.org/docs/latest/tutorial/devtools-extension)

## License

Part of the SPtrader project.

---

*Documentation created by Claude, May 31, 2025*