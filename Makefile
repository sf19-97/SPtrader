# SPtrader Makefile

# Variables
BINARY_NAME=sptrader-api
MAIN_PATH=cmd/api/main.go
BUILD_DIR=build
GO=go
GOFLAGS=-v
LDFLAGS=-w -s

# Build targets
.PHONY: all build clean test run deps lint fmt

all: clean deps build

build:
	@echo "Building $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	$(GO) build $(GOFLAGS) -ldflags="$(LDFLAGS)" -o $(BUILD_DIR)/$(BINARY_NAME) $(MAIN_PATH)
	@echo "Build complete: $(BUILD_DIR)/$(BINARY_NAME)"

clean:
	@echo "Cleaning..."
	@rm -rf $(BUILD_DIR)
	@$(GO) clean

deps:
	@echo "Downloading dependencies..."
	$(GO) mod download
	$(GO) mod tidy

run: build
	@echo "Running $(BINARY_NAME)..."
	./$(BUILD_DIR)/$(BINARY_NAME)

dev:
	@echo "Running in development mode..."
	$(GO) run $(MAIN_PATH)

test:
	@echo "Running tests..."
	$(GO) test -v ./...

test-coverage:
	@echo "Running tests with coverage..."
	$(GO) test -v -coverprofile=coverage.out ./...
	$(GO) tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report: coverage.html"

lint:
	@echo "Running linter..."
	@if command -v golangci-lint >/dev/null 2>&1; then \
		golangci-lint run; \
	else \
		echo "golangci-lint not installed. Install with: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"; \
	fi

fmt:
	@echo "Formatting code..."
	$(GO) fmt ./...

# Database operations
db-migrate:
	@echo "Running database migrations..."
	# Add migration commands here

# Docker operations
docker-build:
	@echo "Building Docker image..."
	docker build -t sptrader-api:latest .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8080:8080 --env-file .env sptrader-api:latest

# Development helpers
generate:
	@echo "Running go generate..."
	$(GO) generate ./...

vendor:
	@echo "Vendoring dependencies..."
	$(GO) mod vendor

# Installation
install: build
	@echo "Installing $(BINARY_NAME)..."
	@cp $(BUILD_DIR)/$(BINARY_NAME) /usr/local/bin/
	@echo "Installed to /usr/local/bin/$(BINARY_NAME)"

uninstall:
	@echo "Uninstalling $(BINARY_NAME)..."
	@rm -f /usr/local/bin/$(BINARY_NAME)

# Help
help:
	@echo "Available targets:"
	@echo "  make build      - Build the binary"
	@echo "  make run        - Build and run"
	@echo "  make dev        - Run in development mode"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make deps       - Download dependencies"
	@echo "  make lint       - Run linter"
	@echo "  make fmt        - Format code"
	@echo "  make install    - Install binary to /usr/local/bin"