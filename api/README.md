# Backend Services

This directory contains the backend services that power our multi-bot platform. It consists of two main components:

## 1. Main API Service (`main_api.py`)

The central service that handles all bot logic and integrations. It acts as a unified interface for all communication platforms (Slack, Discord, OpenChat).

### Key Features
- Bot command processing
- Integration management (GitHub, Asana)
- Cross-platform message handling
- Bot response formatting

### Documentation
- [API Documentation](./API.md) - Detailed API endpoints and usage
- [Main API Source](./main_api.py) - Implementation details

## 2. Storage API Service (`icp_rust_agent/`)

A Rust-based storage service using Internet Computer Protocol (ICP) for secure and decentralized data persistence.

### Key Features
- User data management
- Message history storage
- Integration credentials storage
- Task and issue tracking

### Documentation
- [Storage API Documentation](./icp_rust_agent/API.md) - Detailed API endpoints and usage
- [Rust Implementation](./icp_rust_agent/src/) - Source code and implementation details

## Directory Structure
```
api/
│
├── main_api.py           # Main API service implementation
├── API.md               # Main API documentation
├── requirements.txt     # Python dependencies
├── tokens/             # Token storage directory
│
└── icp_rust_agent/     # Storage API service
    ├── src/           # Rust source code
    ├── Cargo.toml     # Rust dependencies
    ├── API.md         # Storage API documentation
    └── target/        # Build artifacts
```

## Development

### Prerequisites
- Python 3.8+
- Rust 1.70+
- Internet Computer SDK (for storage service)

### Setup

1. **Main API Service**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Run the service
   python -m api.main_api
   ```

2. **Storage API Service**
   ```bash
   cd icp_rust_agent

   # Install Rust dependencies
   cargo build

   # Run the service
   cargo run
   ```

### Environment Variables
Create a `.env` file in the root directory with:
```
# Main API
API_KEY=your-api-key
```

## Production Deployment

### Main API Service
- **URL**: http://154.38.174.112:5005
- **Health Check**: `/api/health`
- **Documentation**: [API.md](./API.md)

### Storage API Service
- **URL**: http://154.38.174.112:3000
- **Authentication**: API key required
- **Documentation**: [icp_rust_agent/API.md](./icp_rust_agent/API.md)