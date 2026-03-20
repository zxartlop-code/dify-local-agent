@echo off
rem start.bat - Start Conway's Game of Life services with Docker Compose

echo === Conway's Game of Life - Docker Compose startup ===

echo Building images...
docker compose build
if %ERRORLEVEL% neq 0 (
    echo Error: Docker Compose build failed.
    exit /b %ERRORLEVEL%
)

echo Starting services (detached)...
docker compose up --detach
if %ERRORLEVEL% neq 0 (
    echo Error: Docker Compose failed to start.
    exit /b %ERRORLEVEL%
)

echo Service status:
docker compose ps
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to check Docker Compose services status.
    exit /b %ERRORLEVEL%
)

echo.
echo Ready!
echo   Frontend  : http://localhost:3000
echo   API docs  : http://localhost:8000/docs
echo   API health: http://localhost:8000/health
echo.
echo   To stop:  docker compose down
echo   To logs:  docker compose logs -f
echo Done!