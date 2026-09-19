@echo off
echo =========================================
echo   Deploying PaperMind Services (Windows)
echo =========================================

REM 1. Ensure .env exists
if not exist .env (
    echo No .env file found. Creating from .env.example...
    copy .env.example .env
)

REM 2. Launch Docker Compose
echo Building and launching containers via Docker Compose...
docker compose down --remove-orphans
docker compose up --build -d

echo.
echo =========================================
echo   PaperMind Deployment Finished!
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000
echo   Swagger Docs: http://localhost:8000/docs
echo =========================================
pause
