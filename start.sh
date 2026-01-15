#!/bin/bash

echo "=========================================="
echo "OTP Authentication Service - Quick Start"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[*] Creating .env from template..."
    cp .env.template .env
    echo "[!] Please edit .env and set SECRET_KEY and other variables"
    echo "[!] Generate SECRET_KEY with: python -c \"import secrets; print(secrets.token_urlsafe(50))\""
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] docker-compose is not installed"
    exit 1
fi

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker daemon is not running"
    exit 1
fi

echo "[*] Starting all services with docker-compose..."
echo ""
echo "Services will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Swagger UI: http://localhost:8000/api/docs/"
echo "  - ReDoc: http://localhost:8000/api/redoc/"
echo "  - Admin: http://localhost:8000/admin/"
echo ""
echo "Starting in 5 seconds... (Ctrl+C to cancel)"
sleep 5

docker-compose up --build

echo ""
echo "=========================================="
echo "Services stopped"
echo "=========================================="
