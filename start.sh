#!/bin/bash
#
# Soccer-AI Startup Script
# Launches both backend (FastAPI) and frontend (Flask) servers
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/flask-frontend"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}       Soccer-AI Server Startup         ${NC}"
echo -e "${BLUE}========================================${NC}"

# Kill any existing instances
echo -e "${YELLOW}Stopping any existing servers...${NC}"
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "flask run" 2>/dev/null
pkill -f "python.*app.py" 2>/dev/null
sleep 1

# Start FastAPI backend
echo -e "${GREEN}Starting FastAPI backend on port 8000...${NC}"
cd "$BACKEND_DIR"
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Wait for backend to initialize
sleep 2

# Start Flask frontend
echo -e "${GREEN}Starting Flask frontend on port 5000...${NC}"
cd "$FRONTEND_DIR"
python app.py &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

# Wait for frontend to initialize
sleep 2

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Soccer-AI is running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "  Backend API:  ${GREEN}http://localhost:8000${NC}"
echo -e "  Frontend UI:  ${GREEN}http://localhost:5000${NC}"
echo -e "  API Docs:     ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Trap Ctrl+C to clean up
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Servers stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait
