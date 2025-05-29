#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to display warning
display_warning() {
    echo -e "\n${RED}${BOLD}⚠️  IMPORTANT WARNING ⚠️${NC}"
    echo -e "${RED}${BOLD}===============================================${NC}"
    echo -e "${RED}The backend canister will expire in 20 minutes!${NC}"
    echo -e "${RED}Please re-deploy after 10-15 minutes maximum${NC}"
    echo -e "${RED}to avoid disrupting your workflow.${NC}"
    echo -e "${RED}${BOLD}===============================================${NC}\n"
}

# Run the deployment script
echo -e "${GREEN}🚀 Starting deployment...${NC}"
"$SCRIPT_DIR/deploy_playground.sh"

# Display warning
display_warning

# Run the service
echo -e "${GREEN}🚀 Starting the service...${NC}"
cd "$PROJECT_ROOT" && cargo run 