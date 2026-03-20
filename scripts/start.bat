@echo off
rem Start Docker Compose services for Dify

echo Starting Docker Compose services for Dify...

rem Run Docker Compose up with error checking
docker-compose up --detach

if %ERRORLEVEL% neq 0 (
    echo Error: Docker Compose failed to start.
    exit /b %ERRORLEVEL%
)

echo Docker Compose services started successfully.

rem Optionally, you can add commands to check the status of the services
echo Checking the status of Docker Compose services...
docker-compose ps

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to check Docker Compose services status.
    exit /b %ERRORLEVEL%
)

echo Done!