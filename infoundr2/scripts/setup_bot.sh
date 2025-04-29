#!/bin/bash

# Exit on error
set -e

echo "Setting up OpenChat offchain bot environment..."

# Step 1: Create new identity
echo "Creating new identity 'infoundr2_identity'..."
dfx identity new infoundr2_identity --storage-mode=plaintext

# Step 2: Export identity to PEM file
echo "Exporting identity to PEM file..."
dfx identity export infoundr2_identity > identity.pem

# Step 3: Get OpenChat public key
echo "Fetching OpenChat public key..."
OC_PUBLIC_KEY=$(curl -s https://oc.app/public-key)

# Step 4: Create config.toml
echo "Creating config.toml..."
cat > config.toml << EOF
pem_file = "./identity.pem"
ic_url = "https://icp0.io"
port = 13457
oc_public_key = """
$OC_PUBLIC_KEY
"""
log_level = "INFO"
EOF

echo "Configuration file created successfully!"

# Step 5: Build the bot
echo "Building the bot..."
cargo build 

echo "Setup complete!" 