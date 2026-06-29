"""
DocFinder Frontend Server
Serves HTML/CSS/JS frontend and proxies API requests to backend.
"""
import os
import sys
import http.server
import socketserver
import json
import re
from urllib.parse import urlparse, parse_qs

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORT = int(os.environ.get('PORT', 3000))
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')

class DocFinderHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def proxy_request(self, method):
        """Proxy request to backend."""
        import urllib.request
        import urllib.error
        
        # Parse the path
        parsed = urlparse(self.path)
        
        # Build backend URL (keep /api prefix)
        backend_url = f"{BACKEND_URL}{parsed.path}"
        if parsed.query:
            backend_url += f"?{parsed.query}"
        
        # Read body if present
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Prepare headers
        headers = {}
        for key, value in self.headers.items():
            if key.lower() not in ['host', 'connection', 'content-length']:
                headers[key] = value
        
        # Make request
        try:
            req = urllib.request.Request(
                backend_url,
                data=body,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req, timeout=180) as response:
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in ['transfer-encoding', 'connection', 'content-length']:
                        self.send_header(key, value)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_body = json.dumps({"detail": str(e)}).encode()
            self.wfile.write(error_body)
            
        except Exception as e:
            self.send_response(502)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_body = json.dumps({"detail": f"Backend error: {str(e)}"}).encode()
            self.wfile.write(error_body)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/api/config':
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            # Convert HTTP URL to WS URL
            ws_url = BACKEND_URL.replace('http://', 'ws://').replace('https://', 'wss://')
            config = {
                "backend_url": BACKEND_URL,
                "ws_url": ws_url
            }
            self.wfile.write(json.dumps(config).encode())
            return

        if self.path.startswith('/api/'):
            return self.proxy_request('GET')
        # Serve index.html for root
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/portal':
            self.path = '/portal.html'
            
        # Call super, but we need to inject cache headers
        super().do_GET()
        
    def end_headers(self):
        # Inject cache busting for HTML files
        if self.path.endswith('.html') or self.path.endswith('.js') or self.path.endswith('.css'):
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            return self.proxy_request('POST')
        return super().do_POST()
    
    def do_PUT(self):
        if self.path.startswith('/api/'):
            return self.proxy_request('PUT')
        return super().do_PUT()
    
    def do_DELETE(self):
        if self.path.startswith('/api/'):
            return self.proxy_request('DELETE')
        return super().do_DELETE()
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")
    
    def do_HEAD(self):
        print(f"[DEBUG HEAD] {self.path}")
        if self.path.startswith('/api/'):
            return self.proxy_request('HEAD')
        return super().do_HEAD()

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🚀 DocFinder Frontend Server                          ║
║                                                          ║
║   Frontend: http://localhost:{PORT}                       ║
║   Backend:  {BACKEND_URL}                       ║
║                                                          ║
║   Press Ctrl+C to stop                                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    with socketserver.ThreadingTCPServer(("", PORT), DocFinderHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
