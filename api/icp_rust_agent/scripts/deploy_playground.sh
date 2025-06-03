#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🚀 Starting playground deployment for storage API...${NC}"

# Check if we're in the correct directory
if [ ! -f "$PROJECT_ROOT/Cargo.toml" ]; then
    echo -e "${YELLOW}❌ Please run this script from the icp_rust_agent directory${NC}"
    exit 1
fi

# Create a temporary directory for the backend deployment
TEMP_DIR=$(mktemp -d)
echo -e "${GREEN}📦 Creating temporary directory for backend deployment...${NC}"

# Clone the infoundr-site repository
echo -e "${GREEN}📥 Cloning infoundr-site repository...${NC}"
git clone https://github.com/Infoundr/infoundr-site.git "$TEMP_DIR"

# Navigate to the backend directory
cd "$TEMP_DIR"

# Ensure assetstorage.did exists for frontend
if [ ! -f "$TEMP_DIR/frontend/assetstorage.did" ]; then
    echo -e "${YELLOW}⚠️  Creating missing frontend/assetstorage.did...${NC}"
    cat > "$TEMP_DIR/frontend/assetstorage.did" <<EOL
service : () -> () {}
EOL
fi

# Install dependencies
echo -e "${GREEN}📦 Installing dependencies...${NC}"
cd "$TEMP_DIR"
npm install
cd "$TEMP_DIR/src/frontend"
npm install

# Deploy the backend canisters to playground
echo -e "${GREEN}📦 Deploying backend canisters to Internet Computer Playground...${NC}"
cd "$TEMP_DIR"
npm run dev:playground

# Extract the backend canister ID from the deployment output
CANISTER_ID=$(dfx canister --playground id backend)
echo -e "${GREEN}✅ Retrieved backend canister ID: ${YELLOW}$CANISTER_ID${NC}"

# Return to the original directory
cd - > /dev/null

# Update the canister ID in main.rs
echo -e "${GREEN}📝 Updating canister ID in main.rs...${NC}"

# Create a backup of the original file
cp "$PROJECT_ROOT/src/main.rs" "$PROJECT_ROOT/src/main.rs.bak"

# Replace only the canister ID value, preserving the rest of the line structure
sed -i '' -e "s/\"[a-z0-9-]*\"; \/\/ testnet/\"$CANISTER_ID\"; \/\/ testnet/" "$PROJECT_ROOT/src/main.rs"

# Clean up
echo -e "${GREEN}🧹 Cleaning up temporary files...${NC}"
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update the API_KEY in the .env file with your actual API key"
echo "2. Run the service with: cargo run"
echo "3. The service will be available at: http://localhost:3000"
echo -e "${YELLOW}Note:${NC} The backend canister is now deployed at: https://$CANISTER_ID.icp0.io" 