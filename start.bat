@echo off
REM Quick start script for OTP Authentication Service (Windows)

echo ==========================================
echo OTP Authentication Service - Quick Start
echo ==========================================
echo.

if not exist .env (
    echo [*] Creating .env from template...
    copy .env.template .env
    echo [!] Please edit .env and set SECRET_KEY and other variables
    echo [!] Generate SECRET_KEY with: python -c "import secrets; print(secrets.token_urlsafe(50))"
    exit /b 1
)

echo [*] Starting all services with docker-compose...
echo.
echo Services will be available at:
echo   - API: http://localhost:8000
echo   - Swagger UI: http://localhost:8000/api/docs/
echo   - ReDoc: http://localhost:8000/api/redoc/
echo   - Admin: http://localhost:8000/admin/
echo.
echo Starting in 5 seconds... (Ctrl+C to cancel)
timeout /t 5 /nobreak

docker-compose up --build

echo.
echo ==========================================
echo Services stopped
echo ==========================================
