#!/bin/bash
set -e

echo "========================================="
echo "  Deploying PaperMind Services"
echo "========================================="

# 1. Ensure .env exists
if [ ! -f .env ]; then
  echo "No .env file found. Creating from .env.example..."
  cp .env.example .env
fi

# 2. Check Docker
if ! command -v docker &> /dev/null; then
  echo "Error: docker is not installed. Please install Docker and Docker Compose."
  exit 1
fi

# 3. Build and launch containers
echo "Building and launching containers via Docker Compose..."
docker compose down --remove-orphans
docker compose up --build -d

echo "Waiting for services to become healthy..."
sleep 5

# 4. Check Health
curl -s http://localhost:8000/health || true

echo ""
echo "========================================="
echo "  PaperMind Deployed Successfully!"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  Swagger Docs: http://localhost:8000/docs"
echo "========================================="
