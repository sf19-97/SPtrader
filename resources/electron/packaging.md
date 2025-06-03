# Electron Packaging and Distribution Guide

## Overview

Packaging an Electron application involves bundling your code, dependencies, and the Electron runtime into a distributable format for different platforms. This guide covers the entire packaging and distribution workflow.

## Prerequisites

Before packaging, ensure your app meets these requirements:

1. Functional `package.json` with correct dependencies
2. Main process entry point defined in `package.json` (`main` field)
3. All assets and resources properly referenced with relative paths
4. Appropriate app icons for each platform

## Popular Packaging Tools

### 1. Electron Builder (Recommended)

Electron Builder provides a complete solution for packaging and distributing Electron applications.

#### Installation

```bash
npm install electron-builder --save-dev
```

#### Basic Configuration

Add to `package.json`:

```json
{
  "name": "your-app",
  "version": "1.0.0",
  "description": "Your app description",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder"
  },
  "build": {
    "appId": "com.example.yourapp",
    "productName": "Your App Name",
    "directories": {
      "output": "dist"
    },
    "files": [
      "**/*",
      "!**/node_modules/*/{CHANGELOG.md,README.md,README,readme.md,readme}",
      "!**/node_modules/*/{test,__tests__,tests,powered-test,example,examples}",
      "!**/node_modules/.bin",
      "!**/*.{iml,o,hprof,orig,pyc,pyo,rbc,swp,csproj,sln,xproj}",
      "!.editorconfig",
      "!**/._*",
      "!**/{.DS_Store,.git,.hg,.svn,CVS,RCS,SCCS,.gitignore,.gitattributes}",
      "!**/{__pycache__,thumbs.db,.flowconfig,.idea,.vs,.nyc_output}",
      "!**/{appveyor.yml,.travis.yml,circle.yml}",
      "!**/{npm-debug.log,yarn.lock,.yarn-integrity,.yarn-metadata.json}"
    ],
    "mac": {
      "category": "public.app-category.utilities",
      "target": ["dmg", "zip"]
    },
    "win": {
      "target": ["nsis", "portable"]
    },
    "linux": {
      "target": ["AppImage", "deb"],
      "category": "Utility"
    }
  },
  "devDependencies": {
    "electron": "^25.0.0",
    "electron-builder": "^24.0.0"
  }
}
```

#### Building for All Platforms

```bash
# Build for current platform
npm run build

# Build for specific platforms
npx electron-builder --mac
npx electron-builder --win
npx electron-builder --linux
```

### 2. Electron Forge

Another popular option, especially good for beginners.

#### Installation

```bash
npm install --save-dev @electron-forge/cli
npx electron-forge import
```

#### Configuration

A basic `forge.config.js`:

```javascript
module.exports = {
  packagerConfig: {
    asar: true,
    icon: './assets/icon' // no extension required
  },
  rebuildConfig: {},
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {},
    },
    {
      name: '@electron-forge/maker-zip',
      platforms: ['darwin'],
    },
    {
      name: '@electron-forge/maker-deb',
      config: {},
    },
    {
      name: '@electron-forge/maker-rpm',
      config: {},
    },
  ],
  publishers: [
    {
      name: '@electron-forge/publisher-github',
      config: {
        repository: {
          owner: 'your-github-username',
          name: 'your-repo-name'
        },
        prerelease: false
      }
    }
  ]
};
```

#### Building with Forge

```bash
npm run make
```

## Platform-Specific Considerations

### Windows

#### Code Signing

Code signing is essential for Windows to avoid security warnings:

```json
{
  "build": {
    "win": {
      "certificateFile": "path/to/certificate.pfx",
      "certificatePassword": "your-password",
      "signingHashAlgorithms": ["sha256"],
      "verifyUpdateCodeSignature": true
    }
  }
}
```

For CI/CD, use environment variables:

```json
{
  "build": {
    "win": {
      "certificateSubjectName": "Your Company, Inc.",
      "certificateSha1": "CERTIFICATE_FINGERPRINT",
      "signingHashAlgorithms": ["sha256"]
    }
  }
}
```

#### Installer Options (NSIS)

Customize the Windows installer:

```json
{
  "build": {
    "win": {
      "target": "nsis"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "shortcutName": "Your App",
      "perMachine": false,
      "installerIcon": "build/icon.ico",
      "uninstallerIcon": "build/icon.ico",
      "installerHeaderIcon": "build/icon.ico",
      "deleteAppDataOnUninstall": true
    }
  }
}
```

### macOS

#### Notarization

Notarization is required for macOS distribution outside the App Store:

```json
{
  "build": {
    "mac": {
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "build/entitlements.mac.plist",
      "entitlementsInherit": "build/entitlements.mac.inherit.plist",
      "notarize": true
    },
    "afterSign": "scripts/notarize.js"
  }
}
```

Create a notarization script (`scripts/notarize.js`):

```javascript
const { notarize } = require('electron-notarize');

exports.default = async function notarizing(context) {
  const { electronPlatformName, appOutDir } = context;  
  if (electronPlatformName !== 'darwin') {
    return;
  }

  const appName = context.packager.appInfo.productFilename;

  return await notarize({
    appBundleId: 'com.example.yourapp',
    appPath: `${appOutDir}/${appName}.app`,
    appleId: process.env.APPLE_ID,
    appleIdPassword: process.env.APPLE_ID_PASSWORD,
    teamId: process.env.APPLE_TEAM_ID,
  });
};
```

#### DMG Configuration

Customize the DMG installer:

```json
{
  "build": {
    "mac": {
      "target": ["dmg", "zip"]
    },
    "dmg": {
      "contents": [
        {
          "x": 130,
          "y": 220
        },
        {
          "x": 410,
          "y": 220,
          "type": "link",
          "path": "/Applications"
        }
      ],
      "window": {
        "width": 540,
        "height": 380
      },
      "backgroundColor": "#ffffff",
      "icon": "build/icon.icns"
    }
  }
}
```

### Linux

#### AppImage Options

```json
{
  "build": {
    "linux": {
      "target": ["AppImage"],
      "category": "Utility",
      "synopsis": "Short description",
      "description": "Longer description",
      "desktop": {
        "Name": "Your App",
        "Comment": "Your app description",
        "GenericName": "Utility",
        "Terminal": false,
        "Type": "Application",
        "Categories": "Utility;"
      },
      "executableName": "your-app"
    },
    "appImage": {
      "license": "license.txt"
    }
  }
}
```

#### Debian/Ubuntu Packages

```json
{
  "build": {
    "linux": {
      "target": ["deb"],
      "maintainer": "Your Name <your.email@example.com>",
      "vendor": "Your Company",
      "depends": ["libnotify4", "libxtst6"]
    },
    "deb": {
      "afterInstall": "scripts/debian-post-install.sh",
      "afterRemove": "scripts/debian-post-remove.sh",
      "fpm": ["--deb-no-default-config-files"]
    }
  }
}
```

## App Icon Configuration

Icons need to be in the right format for each platform:

```json
{
  "build": {
    "appId": "com.example.yourapp",
    "productName": "Your App Name",
    "mac": {
      "icon": "build/icons/icon.icns"
    },
    "win": {
      "icon": "build/icons/icon.ico"
    },
    "linux": {
      "icon": "build/icons"
    }
  }
}
```

Recommended icon sizes:
- Windows: `.ico` file (256x256 pixels)
- macOS: `.icns` file (1024x1024 pixels)
- Linux: Directory with PNG files of sizes 16x16, 32x32, 48x48, 64x64, 128x128, 256x256, 512x512, and 1024x1024

## Auto-Update Configuration

### Using electron-updater

```javascript
// In main.js
const { app, autoUpdater, dialog } = require('electron')
const { autoUpdater } = require('electron-updater')

// Configure logging
autoUpdater.logger = require('electron-log')
autoUpdater.logger.transports.file.level = 'info'

// Configure update server
autoUpdater.setFeedURL({
  provider: 'github',
  owner: 'your-username',
  repo: 'your-repo',
  private: false
})

// Check for updates
app.on('ready', () => {
  autoUpdater.checkForUpdatesAndNotify()
})

// Listen for update events
autoUpdater.on('update-available', (info) => {
  // Notify user of available update
})

autoUpdater.on('update-downloaded', (info) => {
  // Prompt user to install update
  dialog.showMessageBox({
    type: 'info',
    title: 'Update Ready',
    message: 'A new version has been downloaded. Restart the application to apply the updates.',
    buttons: ['Restart', 'Later']
  }).then((returnValue) => {
    if (returnValue.response === 0) {
      autoUpdater.quitAndInstall()
    }
  })
})

autoUpdater.on('error', (err) => {
  console.error('Update error:', err)
})
```

### In package.json

```json
{
  "build": {
    "publish": [
      {
        "provider": "github",
        "owner": "your-username",
        "repo": "your-repo"
      }
    ]
  }
}
```

## Advanced Configurations

### Managing Dependencies

Control which dependencies are bundled:

```json
{
  "build": {
    "files": [
      "**/*",
      "!node_modules/unnecessary-package/**/*"
    ],
    "extraResources": [
      {
        "from": "resources/",
        "to": "resources/"
      }
    ],
    "extraFiles": [
      "license.txt"
    ]
  }
}
```

### ASAR Configuration

Control ASAR packaging:

```json
{
  "build": {
    "asar": true,
    "asarUnpack": [
      "**/*.node",
      "**/*.dll",
      "**/node_modules/sharp/**/*"
    ]
  }
}
```

### Custom Build Hooks

Execute scripts during the build process:

```json
{
  "build": {
    "beforeBuild": "./scripts/before-build.js",
    "afterBuild": "./scripts/after-build.js",
    "afterSign": "./scripts/after-sign.js",
    "afterPack": "./scripts/after-pack.js"
  }
}
```

## CI/CD Integration

### GitHub Actions Example

`.github/workflows/build.yml`:

```yaml
name: Build

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  release:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [macos-latest, ubuntu-latest, windows-latest]

    steps:
      - name: Check out Git repository
        uses: actions/checkout@v3

      - name: Install Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Build/release Electron app
        uses: samuelmeuli/action-electron-builder@v1
        with:
          # GitHub token for auto-publishing
          github_token: ${{ secrets.GITHUB_TOKEN }}
          # If the commit is tagged with a version
          release: ${{ startsWith(github.ref, 'refs/tags/v') }}
          # Code signing for macOS
          mac_certs: ${{ secrets.MAC_CERTS }}
          mac_certs_password: ${{ secrets.MAC_CERTS_PASSWORD }}
          # Code signing for Windows
          windows_certs: ${{ secrets.WINDOWS_CERTS }}
          windows_certs_password: ${{ secrets.WINDOWS_CERTS_PASSWORD }}
```

## Distribution Channels

### 1. Direct Download

Host installers on your website or file hosting service.

### 2. App Stores

#### Mac App Store

Requirements:
- Apple Developer Account ($99/year)
- App notarization
- Sandbox compliance
- App Store review approval

Configuration:

```json
{
  "build": {
    "mac": {
      "target": ["mas"],
      "category": "public.app-category.utilities",
      "entitlements": "build/entitlements.mas.plist",
      "entitlementsInherit": "build/entitlements.mas.inherit.plist",
      "hardenedRuntime": false
    },
    "mas": {
      "type": "distribution",
      "category": "public.app-category.utilities",
      "entitlements": "build/entitlements.mas.plist",
      "entitlementsInherit": "build/entitlements.mas.inherit.plist",
      "provisioningProfile": "embedded.provisionprofile"
    }
  }
}
```

#### Microsoft Store

Requirements:
- Microsoft Developer Account ($19 one-time fee for individuals)
- App certification
- Store review approval

Use the Windows App Certification Kit (WACK) to test compliance.

### 3. GitHub Releases

Electron Builder can automatically publish to GitHub Releases:

```json
{
  "build": {
    "publish": [
      {
        "provider": "github",
        "owner": "your-username",
        "repo": "your-repo",
        "private": false,
        "releaseType": "release"
      }
    ]
  }
}
```

Then publish:

```bash
# Set GH_TOKEN environment variable first
GH_TOKEN=your_github_token electron-builder --publish always
```

## Best Practices

1. **Version management**: Use semantic versioning (`MAJOR.MINOR.PATCH`)
2. **Test packages**: Always test built packages before distribution
3. **Keep builds reproducible**: Use lockfiles (package-lock.json, yarn.lock)
4. **Secure signing keys**: Store signing certificates securely
5. **Release notes**: Maintain detailed release notes for each version
6. **Progressive rollout**: Consider phased rollouts for auto-updates
7. **Telemetry**: Add crash reporting and anonymous usage statistics
8. **Backup artifacts**: Keep build artifacts in secure storage
9. **Test on all platforms**: Verify functionality on all target platforms
10. **Minimize package size**: Remove unnecessary files and optimize assets