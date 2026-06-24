#!/usr/bin/env python3
"""
DocFinder Startup Script
Starts backend and frontend with proper error handling.
Cross-platform compatible version.
"""
import os
import sys
import time
import subprocess
import requests
from datetime import datetime

# Force UTF-8 encoding for Windows console to handle emojis/box drawing
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Colors
try:
    import colorama
    colorama.init()
except ImportError:
    pass

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Dynamic Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCFINDER_DIR = os.path.join(BASE_DIR, 'docfinder')
FRONTEND_DIR = os.path.join(BASE_DIR, 'docfinder_frontend')
BACKEND_LOG = os.path.join(BASE_DIR, 'backend.log')
FRONTEND_LOG = os.path.join(BASE_DIR, 'frontend.log')

def log(msg, color=RESET):
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {msg}{RESET}")

def check_port(port):
    """Check if port is in use."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def wait_for_service(url, name, max_attempts=10):
    """Wait for service to be ready."""
    for i in range(max_attempts):
        try:
            r = requests.get(url, timeout=2)
            return True
        except:
            time.sleep(1)
    return False

def start_backend():
    """Start the FastAPI backend."""
    log("Starting backend on port 8000...", BLUE)
    
    if check_port(8000):
        log("Backend already running on port 8000", YELLOW)
        return True
    
    os.chdir(DOCFINDER_DIR)
    
    # We use sys.executable to run the current python environment
    cmd = [
        sys.executable,
        '-m', 'uvicorn', 
        'main:app',
        '--host', '0.0.0.0',
        '--port', '8000'
    ]
    
    try:
        with open(BACKEND_LOG, 'w') as f:
            proc = subprocess.Popen(cmd, stdout=f, stderr=f)
            for _ in range(30):
                try:
                    import urllib.request
                    urllib.request.urlopen("http://localhost:8000/health")
                    log("Backend started successfully!", GREEN)
                    return True
                except:
                    time.sleep(1)
            log("Backend failed to start - check backend.log", RED)
            return False
    except Exception as e:
        log(f"Backend error: {e}", RED)
        return False

def start_frontend():
    """Start the HTML frontend server."""
    log("Starting frontend on port 3000...", BLUE)
    
    if check_port(3000):
        log("Frontend already running on port 3000", YELLOW)
        return True
    
    os.chdir(FRONTEND_DIR)
    
    cmd = [
        sys.executable,
        'server.py'
    ]
    
    try:
        with open(FRONTEND_LOG, 'w') as f:
            proc = subprocess.Popen(cmd, stdout=f, stderr=f)
        
        time.sleep(2)
        
        if check_port(3000):
            log("Frontend started successfully!", GREEN)
            return True
        else:
            log("Frontend failed to start - check frontend.log", RED)
            return False
    except Exception as e:
        log(f"Frontend error: {e}", RED)
        return False

def test_services():
    """Test all services."""
    log("\nTesting services...", BLUE)
    
    # Test backend
    try:
        r = requests.post(
            'http://localhost:8000/api/login',
            json={'username': 'test', 'password': 'test'},
            timeout=5
        )
        if r.status_code == 401:  # Expected - invalid credentials
            log("✓ Backend API working", GREEN)
        else:
            log(f"✗ Backend returned: {r.status_code}", RED)
    except Exception as e:
        log(f"✗ Backend error: {e}", RED)
    
    # Test frontend
    try:
        r = requests.get('http://localhost:3000', timeout=5)
        if r.status_code == 200:
            log("✓ Frontend serving HTML", GREEN)
        else:
            log(f"✗ Frontend returned: {r.status_code}", RED)
    except Exception as e:
        log(f"✗ Frontend error: {e}", RED)

def kill_processes():
    log("Stopping existing processes...", YELLOW)
    try:
        if os.name == 'nt':
            import psutil
            for proc in psutil.process_iter(['cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any(term in ' '.join(cmdline) for term in ['uvicorn', 'server.py']):
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        else:
            subprocess.run(['pkill', '-f', 'uvicorn'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'server.py'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'streamlit'], stderr=subprocess.DEVNULL)
    except Exception as e:
        log(f"Warning: Failed to kill existing processes: {e}", RED)

def main():
    print(f"""
{BOLD}{BLUE}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🚀 DocFinder - Starting Services                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{RESET}
    """)
    
    # Install psutil if needed for process killing on Windows
    if os.name == 'nt':
        try:
            import psutil
        except ImportError:
            log("Installing psutil...", YELLOW)
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'psutil'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    kill_processes()
    time.sleep(2)
    
    # Start services
    backend_ok = start_backend()
    frontend_ok = start_frontend()
    
    # Test
    test_services()
    
    print(f"""
{BOLD}{GREEN}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ✅ DocFinder Started Successfully!                          ║
║                                                              ║
║   🌐 Frontend:  http://localhost:3000                      ║
║   🔌 Backend:    http://localhost:8000                     ║
║   📚 API Docs:   http://localhost:8000/docs                ║
║                                                              ║
║   Logs:                                                      ║
║   - Backend:  {BACKEND_LOG}
║   - Frontend: {FRONTEND_LOG}
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{RESET}
    """)
    
    if not backend_ok or not frontend_ok:
        log("Some services failed to start. Check logs.", RED)
        sys.exit(1)
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Stopping services...", YELLOW)
        kill_processes()
        sys.exit(0)

if __name__ == '__main__':
    main()

