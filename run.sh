#!/usr/bin/env bash
set -e

# ResuMatch ATS - Quick Start Script

echo "============================================="
echo "  Starting ResuMatch ATS ML & Web Platform   "
echo "============================================="

# Function to stop background processes on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT

# 1. Start Python FastAPI Backend (Port 8000)
echo "[1/2] Starting Python ML API Backend on http://127.0.0.1:8000..."
uv run python api_server.py &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 2

# 2. Start Next.js Frontend (Port 3000)
echo "[2/2] Starting Next.js Web Frontend on http://localhost:3000..."
cd frontend
npm run dev

