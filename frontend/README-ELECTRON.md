# SPtrader Desktop Application

This is the Electron desktop wrapper for the SPtrader frontend.

## Prerequisites

- Node.js and npm installed
- SPtrader backend API running on http://localhost:8080

## Quick Start

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the desktop app:
   ```bash
   ./start-desktop.sh
   ```

   Or manually:
   ```bash
   npm start
   ```

## Development

Run in development mode with DevTools:
```bash
npm run start-dev
```

## Building

To build distributable packages:

```bash
# Build for current platform
npm run build

# Build without publishing
npm run dist
```

## Features

- Full-featured trading chart interface
- Secure API communication with backend
- Native desktop menus
- Resizable window with minimum dimensions
- Dark theme optimized for trading

## Scripts

- `npm start` - Start the Electron app
- `npm run start-dev` - Start with DevTools open
- `npm run start-no-sandbox` - Start without sandbox (for certain Linux environments)
- `npm run build` - Build distributable packages
- `npm run dist` - Build without publishing

## Architecture

- `main.js` - Main Electron process
- `preload.js` - Secure bridge for API communication
- `renderer.js` - Frontend chart rendering logic
- `index.html` - Main application UI

The app connects to the SPtrader backend API at `http://localhost:8080` for all data operations.