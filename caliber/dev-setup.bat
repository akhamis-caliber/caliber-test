@echo off
REM Caliber Development Setup Script for Windows
REM This script provides quick commands for common development tasks

echo 🚀 Caliber Development Environment
echo ==================================

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="--help" goto help
if "%1"=="-h" goto help

if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="workers" goto workers
if "%1"=="test" goto test

echo ❌ Unknown command: %1
echo Use 'dev-setup.bat help' for available commands
exit /b 1

:start
echo 🐳 Starting Docker services...
docker-compose up -d postgres redis backend
echo ✅ Services started
echo 📊 API available at: http://localhost:8000
echo 📚 Docs available at: http://localhost:8000/docs
goto end

:stop
echo 🛑 Stopping Docker services...
docker-compose down
echo ✅ Services stopped
goto end

:restart
echo 🔄 Restarting backend...
docker-compose restart backend
echo ✅ Backend restarted
goto end

:logs
echo 📋 Viewing backend logs...
docker-compose logs -f backend
goto end

:status
echo 📊 Service Status:
docker-compose ps
echo.
echo 🏥 Health Check:
curl -s http://localhost:8000/health
echo.
goto end

:workers
echo 👷 Starting background workers...
docker-compose up -d worker-scoring worker-maintenance scheduler flower
echo ✅ Workers started
echo 📊 Flower monitor available at: http://localhost:5555
goto end

:test
echo 🧪 Running tests...
cd ..
python test_all_modules.py
python test_storage.py
python test_models.py
goto end

:help
echo Usage: dev-setup.bat [command]
echo.
echo Commands:
echo   start     - Start core services (postgres, redis, backend)
echo   stop      - Stop all services
echo   restart   - Restart backend service
echo   logs      - View backend logs
echo   status    - Check service status and health
echo   workers   - Start background workers
echo   test      - Run test suite
echo   help      - Show this help message
echo.
echo Examples:
echo   dev-setup.bat start    # Start development environment
echo   dev-setup.bat status   # Check if everything is running
echo   dev-setup.bat logs     # View backend logs
goto end

:end 