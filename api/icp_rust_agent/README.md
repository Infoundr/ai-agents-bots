# Storage API Service

A Rust-based storage service using Internet Computer Protocol (ICP) for secure and decentralized data persistence. This service handles all data storage operations for the Infoundr platform, including user data, message history, and integration credentials.

## Quick Start

### Deployment

1. Make the deployment script executable:
   ```bash
   chmod +x deploy_playground.sh
   ```

2. Run the deployment script:
   ```bash
   ./deploy_playground.sh
   ```

The script will:
- Clone the backend canisters from the infoundr-site repository
- Deploy the backend canisters to the Internet Computer Playground
- Update the canister ID in the storage API code
- Clean up temporary files

### Configuration

After deployment, update the `.env` file with your API key:
```bash
API_KEY=your-api-key-here
ICP_URL=https://ic0.app
```

### Running the Service

Start the service with:
```bash
cargo run
```

The service will be available at `http://localhost:3000`.

## API Documentation

For detailed API documentation, see [API.md](./API.md).

## Development

### Project Structure
```
icp_rust_agent/
├── src/           # Rust source code
│   ├── main.rs    # Main application entry point
│   └── slack.rs   # Slack-specific functionality
├── Cargo.toml     # Rust dependencies
├── API.md         # API documentation
└── deploy_playground.sh  # Deployment script
```

### Testing

Run the test suite with:
```bash
cargo test
```

## Troubleshooting

1. **Deployment Issues**
   - Ensure dfx is properly installed and configured
   - Check your Internet connection
   - Verify you have sufficient cycles in your playground identity
   - Make sure Node.js and npm are installed
   - Check if you have access to the infoundr-site repository

2. **Runtime Issues**
   - Check the `.env` file configuration
   - Verify the canister ID in `main.rs`
   - Ensure all dependencies are installed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited. 