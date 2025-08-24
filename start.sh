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

# Function to prompt for database credentials
prompt_database_credentials() {
    echo ""
    print_status "Database Configuration Setup"
    echo "=================================="
    
    # Check if credentials are already set via environment variables
    if [ ! -z "$DB_USERNAME" ] && [ ! -z "$DB_PASSWORD" ]; then
        print_status "Using database credentials from environment variables:"
        echo "   Username: $DB_USERNAME"
        echo "   Password: [HIDDEN]"
        DB_USER="$DB_USERNAME"
        DB_PASS="$DB_PASSWORD"
        return
    fi
    
    # Prompt for username
    while true; do
        read -p "Enter PostgreSQL username (default: postgres): " DB_USER
        DB_USER=${DB_USER:-postgres}
        
        if [[ "$DB_USER" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
            break
        else
            print_error "Invalid username. Username must start with a letter or underscore and contain only letters, numbers, and underscores."
        fi
    done
    
    # Prompt for password
    while true; do
        read -s -p "Enter PostgreSQL password: " DB_PASS
        echo
        
        if [ ! -z "$DB_PASS" ]; then
            break
        else
            print_error "Password cannot be empty."
        fi
    done
    
    # Confirm password
    read -s -p "Confirm PostgreSQL password: " DB_PASS_CONFIRM
    echo
    
    if [ "$DB_PASS" != "$DB_PASS_CONFIRM" ]; then
        print_error "Passwords do not match. Please try again."
        exit 1
    fi
    
    print_success "Database credentials set successfully!"
}

# Function to update docker-compose.yml with new credentials
update_docker_compose() {
    print_status "Updating docker-compose.yml with database credentials..."
    
    # Create a backup of the original file
    cp docker-compose.yml docker-compose.yml.backup
    
    # Update the docker-compose.yml file with new credentials
    sed -i.tmp "s/POSTGRES_USER: postgres/POSTGRES_USER: $DB_USER/g" docker-compose.yml
    sed -i.tmp "s/POSTGRES_PASSWORD: password/POSTGRES_PASSWORD: $DB_PASS/g" docker-compose.yml
    
    # Update the backend service DATABASE_URL
    sed -i.tmp "s|DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/lender_framework|DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASS@postgres:5432/lender_framework|g" docker-compose.yml
    
    # Update the celery worker DATABASE_URL
    sed -i.tmp "s|DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/lender_framework|DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASS@postgres:5432/lender_framework|g" docker-compose.yml
    
    # Remove temporary files
    rm -f docker-compose.yml.tmp
    
    print_success "docker-compose.yml updated successfully!"
}

# Function to restore docker-compose.yml from backup
restore_docker_compose() {
    if [ -f "docker-compose.yml.backup" ]; then
        print_status "Restoring docker-compose.yml from backup..."
        mv docker-compose.yml.backup docker-compose.yml
        print_success "docker-compose.yml restored from backup"
    fi
}

# Set up cleanup on script exit
trap restore_docker_compose EXIT

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

# Prompt for database credentials
prompt_database_credentials

# Update docker-compose.yml with new credentials
update_docker_compose

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

# Check if .env file exists and update it with new credentials
if [ ! -f "backend/.env" ]; then
    print_warning ".env file not found. Creating default .env file..."
    cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASS@localhost:5432/lender_framework

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
    print_success "Created default .env file with new database credentials"
else
    # Update existing .env file with new database credentials
    print_status "Updating existing .env file with new database credentials..."
    sed -i.tmp "s|DATABASE_URL=postgresql+asyncpg://.*@localhost:5432/lender_framework|DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASS@localhost:5432/lender_framework|g" backend/.env
    rm -f backend/.env.tmp
    print_success "Updated .env file with new database credentials"
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

# Check PostgreSQL with new credentials
if docker-compose exec -T postgres pg_isready -U "$DB_USER" > /dev/null 2>&1; then
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

# Remove the exit trap since we're successful
trap - EXIT

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
echo "   • Username:     $DB_USER"
echo "   • Database:     lender_framework"
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
