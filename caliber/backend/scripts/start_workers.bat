@echo off
REM Caliber Worker Management Script for Windows

setlocal enabledelayedexpansion

REM Check if Redis is running
echo [INFO] Checking Redis connection...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Redis is not running. Please start Redis first.
    exit /b 1
)
echo [INFO] Redis is running

REM Create logs directory
if not exist logs mkdir logs
echo [INFO] Created logs directory

REM Start scoring workers
echo [INFO] Starting scoring workers...
start /B celery -A worker.celery worker --loglevel=info --queues=scoring --concurrency=2 --hostname=scoring@%%h --logfile=logs/celery_scoring.log

REM Start maintenance workers
echo [INFO] Starting maintenance workers...
start /B celery -A worker.celery worker --loglevel=info --queues=maintenance,exports,monitoring --concurrency=1 --hostname=maintenance@%%h --logfile=logs/celery_maintenance.log

REM Start beat scheduler
echo [INFO] Starting beat scheduler...
start /B celery -A worker.celery beat --loglevel=info --logfile=logs/celery_beat.log

REM Start flower monitoring
echo [INFO] Starting Flower monitoring...
start /B celery -A worker.celery flower --port=5555 --logfile=logs/celery_flower.log

echo [INFO] All workers started successfully
echo [INFO] Flower monitoring available at: http://localhost:5555 