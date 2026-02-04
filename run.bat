@echo off
REM Environmental Data Pipeline - Windows Helper Script

echo ============================================
echo Environmental Data Pipeline Management
echo ============================================
echo.

if "%1"=="" goto menu
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="clean" goto clean
if "%1"=="rebuild" goto rebuild
goto menu

:menu
echo Available commands:
echo   start    - Start all containers
echo   stop     - Stop all containers
echo   restart  - Restart all containers
echo   logs     - View logs (Ctrl+C to exit)
echo   status   - Check container status
echo   clean    - Stop and remove containers (keeps data)
echo   rebuild  - Rebuild all containers
echo.
echo Usage: run.bat [command]
goto end

:start
echo Starting all containers...
docker-compose up -d
echo.
echo Waiting for services to initialize...
timeout /t 5 /nobreak >nul
docker-compose ps
echo.
echo Dashboard will be available at: http://localhost:8501
echo Database available at: localhost:5432
echo.
echo Use 'run.bat logs' to view container logs
goto end

:stop
echo Stopping all containers...
docker-compose down
goto end

:restart
echo Restarting all containers...
docker-compose restart
goto end

:logs
echo Showing logs (Ctrl+C to exit)...
docker-compose logs -f
goto end

:status
echo Container Status:
docker-compose ps
echo.
echo Network Status:
docker network ls | findstr environmental
echo.
echo Volume Status:
docker volume ls | findstr env_data
goto end

:clean
echo WARNING: This will stop and remove all containers.
echo Data volumes will be preserved.
set /p confirm="Continue? (y/n): "
if /i "%confirm%"=="y" (
    docker-compose down
    echo Cleanup complete.
) else (
    echo Cancelled.
)
goto end

:rebuild
echo Rebuilding all containers...
docker-compose build --no-cache
echo.
echo Build complete. Use 'run.bat start' to launch.
goto end

:end
