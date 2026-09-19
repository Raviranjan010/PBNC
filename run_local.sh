#!/bin/bash
set -e

echo "========================================="
echo "  Starting PaperMind (Local Standalone)"
echo "========================================="

# 1. Copy .env if not present
if [ ! -f .env ]; then
  cp .env.example .env
fi

# 2. Run Alembic migrations
echo "Running database migrations..."
python -m alembic -c backend/alembic.ini upgrade head

# 3. Generate sample fixtures
echo "Checking test fixtures..."
python samples/generate_samples.py

# 4. Start backend
echo "Starting FastAPI Backend at http://127.0.0.1:8000 ..."
uvicorn backend.app.main:app --port 8000 --reload &
BACKEND_PID=$!

trap "kill $BACKEND_PID" EXIT

# 5. Start frontend
echo "Starting Next.js Frontend at http://localhost:3000 ..."
cd frontend && npm run dev
