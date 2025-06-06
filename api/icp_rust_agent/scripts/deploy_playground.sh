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

# Extract the canister IDs from the deployment output
BACKEND_CANISTER_ID=$(dfx canister --playground id backend)
FRONTEND_CANISTER_ID=$(dfx canister --playground id frontend)
echo -e "${GREEN}✅ Retrieved backend canister ID: ${YELLOW}$BACKEND_CANISTER_ID${NC}"
echo -e "${GREEN}✅ Retrieved frontend canister ID: ${YELLOW}$FRONTEND_CANISTER_ID${NC}"

# Update the .env file with the new canister IDs
echo -e "${GREEN}📝 Updating .env file with new canister IDs...${NC}"
ENV_FILE="$PROJECT_ROOT/.env"

# Create .env file if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    touch "$ENV_FILE"
fi

# Update or add BASE_URL and CANISTER_ID in .env file
if grep -q "BASE_URL=" "$ENV_FILE"; then
    # Update existing BASE_URL with frontend canister ID
    sed -i '' "s|BASE_URL=.*|BASE_URL=https://$FRONTEND_CANISTER_ID.icp0.io|" "$ENV_FILE"
else
    # Add new BASE_URL with frontend canister ID
    echo "BASE_URL=https://$FRONTEND_CANISTER_ID.icp0.io" >> "$ENV_FILE"
fi

# Update or add CANISTER_ID (using backend canister ID)
if grep -q "CANISTER_ID=" "$ENV_FILE"; then
    # Update existing CANISTER_ID
    sed -i '' "s|CANISTER_ID=.*|CANISTER_ID=$BACKEND_CANISTER_ID|" "$ENV_FILE"
else
    # Add new CANISTER_ID
    echo "CANISTER_ID=$BACKEND_CANISTER_ID" >> "$ENV_FILE"
fi

# Return to the original directory
cd - > /dev/null

# Update the canister ID in main.rs
echo -e "${GREEN}📝 Updating canister ID in main.rs...${NC}"

# Create a backup of the original file
cp "$PROJECT_ROOT/src/main.rs" "$PROJECT_ROOT/src/main.rs.bak"

# Replace only the canister ID value, preserving the rest of the line structure
sed -i '' -e "s/\"[a-z0-9-]*\"; \/\/ testnet/\"$BACKEND_CANISTER_ID\"; \/\/ testnet/" "$PROJECT_ROOT/src/main.rs"

# Clean up
echo -e "${GREEN}🧹 Cleaning up temporary files...${NC}"
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update the API_KEY in the .env file with your actual API key"
echo "2. Run the service with: cargo run"
echo "3. The service will be available at: http://localhost:3005"
echo -e "${YELLOW}Note:${NC} The backend canister is now deployed at: https://$BACKEND_CANISTER_ID.icp0.io" 