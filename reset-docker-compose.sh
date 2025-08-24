#!/bin/bash

# Reset docker-compose.yml to original state
# This script restores the docker-compose.yml file from backup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔄 Resetting docker-compose.yml to original state..."

# Check if backup exists
if [ ! -f "docker-compose.yml.backup" ]; then
    print_error "No backup file found. Cannot restore original docker-compose.yml"
    exit 1
fi

# Stop any running containers
print_status "Stopping any running containers..."
docker-compose down --remove-orphans

# Restore from backup
print_status "Restoring docker-compose.yml from backup..."
mv docker-compose.yml.backup docker-compose.yml

print_success "docker-compose.yml has been restored to its original state!"
print_status "You can now run start.sh again to set up with new credentials."
