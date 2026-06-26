import socket
import urllib.request
import sys

print("Checking port 8000...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 8000))
if result == 0:
    print("Port 8000 is OPEN!")
    try:
        res = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)
        print("Health status code:", res.status)
        print("Health response:", res.read().decode())
    except Exception as e:
        print("Failed to get /health response:", e)
else:
    print("Port 8000 is CLOSED (code:", result, ")")
sock.close()
