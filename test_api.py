import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'https://docfinder-ai.onrender.com/api/chat', 
    data=b'{"text1":"' + b'A'*50000 + b'","text2":"' + b'B'*50000 + b'","query":"test"}', 
    headers={'Content-Type': 'application/json'}
)

try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code)
    print(e.read().decode())
except Exception as e:
    print('Exception:', str(e))
