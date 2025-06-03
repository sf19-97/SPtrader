# SPtrader Binary Directory

*Created: May 31, 2025*

This directory contains the main executables for the SPtrader application. All binaries have been centralized here for better organization.

## Available Binaries

- `sptrader` - Main CLI tool for managing SPtrader
- `sptrader-api` - API server binary
- `api-binary` - API server binary (alternative build)
- `ingestion` - Data ingestion service

## Usage Scripts

- `start_locked.sh` - Starts SPtrader services with locked ports
- `stop_locked.sh` - Stops running SPtrader services

## Important Note

This directory contains copies of the binaries for reference. For actual deployment, use the locked port scripts from the project root:

```bash
cd ~/SPtrader
./stop_locked.sh && sleep 3 && ./start_locked.sh
```

## Starting the Desktop UI

After starting the services, you can launch the desktop UI with:

```bash
cd ~/SPtrader/frontend
./start-desktop.sh
```