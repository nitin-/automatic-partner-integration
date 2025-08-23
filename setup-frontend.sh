#!/bin/bash

echo "Setting up frontend dependencies..."

# Navigate to frontend directory
cd frontend

# Install dependencies and generate package-lock.json
npm install

echo "Frontend setup complete!"
echo "You can now run: ./start.sh"
