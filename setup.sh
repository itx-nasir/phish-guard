#!/bin/bash

# Phish Guard Setup Script
echo "🛡️  Setting up Phish Guard..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
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

print_status "Docker and Docker Compose are installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_warning "Creating .env file from template"
    if [ -f env.template ]; then
        cp env.template .env
        print_status ".env file created from template"
    elif [ -f .env.example ]; then
        cp .env.example .env
        print_status ".env file created from .env.example"
    else
        print_warning "No template file found, creating basic .env file"
        cat > .env << EOF
# Flask Configuration
SECRET_KEY=development-secret-key-change-me
FLASK_DEBUG=True
FLASK_ENV=development

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Redis Configuration
REDIS_URL=redis://redis:6379/1

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# API Configuration
API_RATE_LIMIT=100 per hour

# React Configuration
REACT_APP_API_URL=http://localhost:5000
EOF
        print_status "Basic .env file created"
    fi
else
    print_status ".env file already exists"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p backend/logs
mkdir -p frontend/build

# Set appropriate permissions
chmod -R 755 backend/uploads
chmod -R 755 backend/logs

print_status "Directories created and permissions set"

# Build and start services
echo ""
echo "🚀 Building and starting services..."

# Check if we should use development or production
if [ "$1" = "prod" ] || [ "$1" = "production" ]; then
    print_status "Starting in production mode..."
    docker-compose -f docker-compose.prod.yml up --build -d
    
    if [ $? -eq 0 ]; then
        print_status "Production services started successfully!"
        print_status "Frontend: http://localhost"
        print_status "Backend API: http://localhost:5000"
        print_status "Redis: localhost:6379"
    else
        print_error "Failed to start production services"
        exit 1
    fi
else
    print_status "Starting in development mode..."
    docker-compose -f docker-compose.dev.yml up --build -d
    
    if [ $? -eq 0 ]; then
        print_status "Development services started successfully!"
        print_status "Frontend: http://localhost:3000"
        print_status "Backend API: http://localhost:5000"
        print_status "Redis: localhost:6379"
    else
        print_error "Failed to start development services"
        exit 1
    fi
fi

# Wait a bit for services to start
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo ""
echo "🔍 Running health checks..."

# Check backend health
if curl -s http://localhost:5000/api/health > /dev/null; then
    print_status "Backend is healthy"
else
    print_warning "Backend health check failed - it might still be starting"
fi

# Check Redis
if docker exec $(docker ps -q -f name=redis) redis-cli ping > /dev/null 2>&1; then
    print_status "Redis is healthy"
else
    print_warning "Redis health check failed"
fi

echo ""
print_status "Setup complete! 🎉"
echo ""
echo "📋 Quick Commands:"
echo "  View logs:           docker-compose -f docker-compose.dev.yml logs -f"
echo "  Stop services:       docker-compose -f docker-compose.dev.yml down"
echo "  Restart services:    docker-compose -f docker-compose.dev.yml restart"
echo "  View status:         docker-compose -f docker-compose.dev.yml ps"
echo ""
echo "📚 API Documentation:"
echo "  Health Check:        GET  http://localhost:5000/api/health"
echo "  Analyze Content:     POST http://localhost:5000/api/analyze/content"
echo "  Analyze File:        POST http://localhost:5000/api/analyze/file"
echo "  Get Results:         GET  http://localhost:5000/api/analysis/<task_id>"
echo ""

# Test the API if requested
if [ "$2" = "test" ]; then
    echo "🧪 Running quick API test..."
    
    # Test health endpoint
    response=$(curl -s -w "%{http_code}" http://localhost:5000/api/health -o /tmp/health_response.json)
    if [ "$response" = "200" ]; then
        print_status "API health check passed"
    else
        print_error "API health check failed (HTTP $response)"
    fi
    
    # Clean up
    rm -f /tmp/health_response.json
fi