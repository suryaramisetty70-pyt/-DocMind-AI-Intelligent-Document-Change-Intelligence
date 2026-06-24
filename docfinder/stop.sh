#!/bin/bash

# DocFinder Stop Script

echo "🛑 Stopping DocFinder..."

# Kill backend
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null
        echo "Backend stopped (PID: $BACKEND_PID)"
    fi
    rm .backend.pid
fi

# Kill frontend
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null
        echo "Frontend stopped (PID: $FRONTEND_PID)"
    fi
    rm .frontend.pid
fi

# Also kill any processes on the ports
lsof -Pi :8000 -sTCP:LISTEN -t 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -Pi :12000 -sTCP:LISTEN -t 2>/dev/null | xargs kill -9 2>/dev/null || true

echo "✅ DocFinder stopped"