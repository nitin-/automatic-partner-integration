#!/bin/bash

# Lender API Integration Framework Startup Script
# This script sets up and starts the entire framework

set -e

echo "🚀 Starting Lender API Integration Framework..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p generated_apis api_templates uploads

# Setup frontend dependencies if package-lock.json doesn't exist
if [ ! -f "frontend/package-lock.json" ]; then
    print_status "Setting up frontend dependencies..."
    cd frontend
    npm install
    cd ..
    print_success "Frontend dependencies installed"
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    print_warning ".env file not found. Creating default .env file..."
    cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/lender_framework

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=true
API_V1_STR=/api/v1
PROJECT_NAME=Lender API Integration Framework

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# File Storage
UPLOAD_DIR=uploads
GENERATED_APIS_DIR=generated_apis
TEMPLATES_DIR=api_templates
EOF
    print_success "Created default .env file"
fi

# Stop any existing containers
print_status "Stopping any existing containers..."
docker-compose down --remove-orphans

# Build and start services
print_status "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if services are running
print_status "Checking service status..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL is ready"
else
    print_error "PostgreSQL is not ready"
    exit 1
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is ready"
else
    print_error "Redis is not ready"
    exit 1
fi

# Check Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API is ready"
else
    print_warning "Backend API is not ready yet, waiting..."
    sleep 10
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API is ready"
    else
        print_error "Backend API is not ready"
        exit 1
    fi
fi

# Check Frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend is ready"
else
    print_warning "Frontend is not ready yet, waiting..."
    sleep 10
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is ready"
    else
        print_error "Frontend is not ready"
        exit 1
    fi
fi

# Display service URLs
echo ""
print_success "🎉 Lender API Integration Framework is now running!"
echo ""
echo "📋 Service URLs:"
echo "   • Frontend:     http://localhost:3000"
echo "   • Backend API:  http://localhost:8000"
echo "   • API Docs:     http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
echo "   • Flower:       http://localhost:5555"
echo ""
echo "🗄️  Database:"
echo "   • PostgreSQL:   localhost:5432"
echo "   • Redis:        localhost:6379"
echo ""
echo "🔧 Management Commands:"
echo "   • View logs:    docker-compose logs -f"
echo "   • Stop:         docker-compose down"
echo "   • Restart:      docker-compose restart"
echo "   • Rebuild:      docker-compose up --build -d"
echo ""

# Optional: Open browser
if command -v xdg-open &> /dev/null; then
    print_status "Opening frontend in browser..."
    xdg-open http://localhost:3000 > /dev/null 2>&1 &
elif command -v open &> /dev/null; then
    print_status "Opening frontend in browser..."
    open http://localhost:3000 > /dev/null 2>&1 &
fi

print_success "Setup complete! Enjoy using the Lender API Integration Framework!"
