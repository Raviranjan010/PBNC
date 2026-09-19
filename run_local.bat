@echo off
echo =========================================
echo   Starting PaperMind (Local Standalone)
echo =========================================

REM 1. Copy .env if not present
if not exist .env (
    copy .env.example .env
)

REM 2. Run Alembic migrations
echo Running database migrations...
python -m alembic -c backend\alembic.ini upgrade head

REM 3. Generate sample fixtures
echo Checking test fixtures...
python samples\generate_samples.py

REM 4. Start backend in background window
echo Starting FastAPI Backend at http://127.0.0.1:8000 ...
start "PaperMind Backend" cmd /k "uvicorn backend.app.main:app --port 8000 --reload"

REM 5. Start frontend
echo Starting Next.js Frontend at http://localhost:3000 ...
cd frontend
npm run dev
