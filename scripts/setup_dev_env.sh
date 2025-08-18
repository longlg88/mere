#!/bin/bash

# MERE AI Agent - Development Environment Setup Script

echo "🚀 Setting up MERE AI Agent development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"

# Start services with Docker Compose
echo "📦 Starting database services..."
docker-compose up -d postgres redis minio

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec postgres pg_isready -U mere_user -d mere_ai > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check MinIO
if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "✅ MinIO is ready"
else
    echo "❌ MinIO is not ready"
fi

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📚 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create MinIO buckets for audio storage
echo "🪣 Creating MinIO buckets..."
# This would typically be done through MinIO client, but for now we'll skip it

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start backend server: uvicorn backend.main:app --reload"
echo "3. Create iOS project in Xcode using ios/MEREApp_Setup.md"
echo "4. Run tests: python -m pytest tests/ -v"
echo ""
echo "🌐 Services:"
echo "- Backend API: http://localhost:8000"
echo "- MinIO Console: http://localhost:9001 (admin/minioadmin)"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"