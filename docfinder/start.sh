#!/bin/bash

# DocFinder Startup Script

echo "🚀 Starting DocFinder..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set environment variables
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
export API_BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install it first."
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Kill any existing processes on ports
echo ""
print_warning "Checking ports..."

# Port 8000 (Backend)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 8000 is in use, killing existing process..."
    lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
fi

# Port 12000 (Frontend)
if lsof -Pi :12000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 12000 is in use, killing existing process..."
    lsof -Pi :12000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
fi

# Start FastAPI backend
echo ""
print_warning "Starting FastAPI backend on port 8000..."
cd "$SCRIPT_DIR"
nohup uvicorn docfinder.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid
print_status "Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
BACKEND_READY=false
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        BACKEND_READY=true
        print_status "Backend is ready!"
        break
    fi
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    print_error "Backend failed to start. Check backend.log for details."
    cat backend.log | tail -20
fi

# Start Streamlit frontend
echo ""
print_warning "Starting Streamlit frontend on port 12000..."
nohup streamlit run docfinder/frontend/app.py --server.port 12000 --server.address 0.0.0.0 --server.headless true > frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > .frontend.pid
print_status "Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to start
FRONTEND_READY=false
for i in {1..30}; do
    if curl -s http://localhost:12000 > /dev/null 2>&1; then
        FRONTEND_READY=true
        print_status "Frontend is ready!"
        break
    fi
    sleep 1
done

if [ "$FRONTEND_READY" = false ]; then
    print_error "Frontend failed to start. Check frontend.log for details."
    cat frontend.log | tail -20
fi

echo ""
echo "========================================="
print_status "DocFinder is running!"
echo "========================================="
echo ""
echo "🔗 Access URLs:"
echo "   Frontend (Streamlit): http://localhost:12000"
echo "   Backend (FastAPI):    http://localhost:8000"
echo "   API Docs (Swagger):   http://localhost:8000/docs"
echo ""
echo "🔐 Default Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📝 Logs:"
echo "   Backend log:  backend.log"
echo "   Frontend log: frontend.log"
echo ""
echo "🛑 To stop:"
echo "   ./stop.sh"
echo ""
echo "========================================="