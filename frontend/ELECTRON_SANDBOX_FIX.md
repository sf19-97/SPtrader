# Electron Sandbox Permission Fix
*Last Updated: May 31, 2025 - 22:30 UTC*

## Overview

The SPtrader desktop app uses Electron to provide a native application experience. However, Electron's security sandbox requires specific file permissions that need to be set up correctly for the application to run properly.

## The Issue

When starting the Electron app, you might encounter this error:

```
The SUID sandbox helper binary was found, but is not configured correctly.
```

This happens because the Electron security sandbox needs special permissions to run properly.

## Solution: Using the Sandbox Fix Script

We've created a script that automatically fixes the sandbox permissions:

```bash
# Navigate to the SPtrader root directory
cd ~/SPtrader

# Run the fix script
scripts/fix_electron_sandbox.sh
```

### What the Script Does

1. Locates the Chrome sandbox binary in your Electron installation
2. Sets the correct owner and permissions using sudo
3. Provides clear error messages if something goes wrong
4. Confirms success when permissions are set correctly

### Alternative: No Sandbox Mode

If you prefer not to use sudo or cannot set the required permissions, you can run Electron in no-sandbox mode:

```bash
# Navigate to the frontend directory
cd ~/SPtrader/frontend

# Run with no-sandbox flag
npm run start -- --no-sandbox
```

## Technical Details

The sandbox permission fix works by:

1. Setting the owner of the chrome-sandbox binary to root:root
2. Setting the SUID bit (4755) which allows it to run with elevated privileges

This is standard practice for Electron applications and is required for the security sandbox to function properly.

## Troubleshooting

If you encounter issues:

1. Make sure you have sudo access
2. Check that the Electron dependencies are installed (`npm install`)
3. Try the no-sandbox alternative if permission setting fails

Created: May 31, 2025

## Status: ✅ FIXED

The sandbox permissions have been successfully applied. The desktop app now runs properly with the security sandbox enabled.