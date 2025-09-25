#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting NVIDIA Inception AI Development Environment${NC}"

# Stop and remove existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# Build and start containers
echo -e "${YELLOW}Building and starting containers...${NC}"
docker-compose up --build

# Keep the script running
wait