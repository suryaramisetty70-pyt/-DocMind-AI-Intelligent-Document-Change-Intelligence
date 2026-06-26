import os
import io
import time
import requests
import json
import numpy as np
from PIL import Image, ImageDraw

API_URL = "http://localhost:8000/api"

# We need an admin token to bypass auth or just a normal token.
token = None
try:
    reg_resp = requests.post(f"{API_URL}/register", json={
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "Password123!"
    })
    if reg_resp.status_code == 200:
        token = reg_resp.json().get("access_token")
        print("Successfully created test user and got token.")
    else:
        print("Failed to register:", reg_resp.text)
        log_resp = requests.post(f"{API_URL}/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if log_resp.status_code == 200:
            token = log_resp.json().get("access_token")
            print("Successfully logged in as admin.")
except Exception as e:
    print(f"Auth error: {e}. Trying to proceed without auth if allowed.")

HEADERS = {"Authorization": f"Bearer {token}"} if token else {}

print("==================================")
print("TESTING 25 DOCUMENT COMPARISONS")
print("==================================")

success_count = 0
total_count = 0

# 1. TEXT (10 pairs)
print("\n--- Testing Text (10 pairs) ---")
for i in range(10):
    total_count += 1
    t1 = f"This is original text document {i}. It has some base content."
    t2 = f"This is modified text document {i}. It has DIFFERENT base content."
    res = requests.post(f"{API_URL}/compare/text", data={"text1": t1, "text2": t2, "level": "word", "use_ai": "false"}, headers=HEADERS)
    if res.status_code == 200:
        print(f"[OK] Text {i+1} OK")
        success_count += 1
    else:
        print(f"[FAILED] Text {i+1} FAILED: {res.status_code}")

# 2. CSV (10 pairs)
print("\n--- Testing CSV (10 pairs) ---")
for i in range(10):
    total_count += 1
    csv1 = f"id,name,value\n1,Test{i},100\n2,Sample,200".encode('utf-8')
    csv2 = f"id,name,value\n1,Test{i},999\n2,Sample,200\n3,New,300".encode('utf-8')
    files = {
        'file1': ('test1.csv', io.BytesIO(csv1), 'text/csv'),
        'file2': ('test2.csv', io.BytesIO(csv2), 'text/csv')
    }
    res = requests.post(f"{API_URL}/compare/csv", files=files, data={"use_ai": "false"}, headers=HEADERS)
    if res.status_code == 200:
        print(f"[OK] CSV {i+1} OK")
        success_count += 1
    else:
        print(f"[FAILED] CSV {i+1} FAILED: {res.status_code}")

# 3. IMAGES (5 pairs)
print("\n--- Testing Images (5 pairs) ---")
for i in range(5):
    total_count += 1
    img1 = Image.new('RGB', (100, 100), color=(255, 0, 0))
    d1 = ImageDraw.Draw(img1)
    d1.text((10,10), f"A{i}", fill=(255,255,0))
    b1 = io.BytesIO()
    img1.save(b1, format='JPEG')
    b1.seek(0)
    
    img2 = Image.new('RGB', (100, 100), color=(255, 0, 0))
    d2 = ImageDraw.Draw(img2)
    d2.text((10,10), f"B{i}", fill=(0,255,255))
    b2 = io.BytesIO()
    img2.save(b2, format='JPEG')
    b2.seek(0)
    
    files = {
        'file1': ('img1.jpg', b1, 'image/jpeg'),
        'file2': ('img2.jpg', b2, 'image/jpeg')
    }
    res = requests.post(f"{API_URL}/compare/image", files=files, data={"use_ai": "false"}, headers=HEADERS)
    if res.status_code == 200:
        print(f"[OK] Image {i+1} OK")
        success_count += 1
    else:
        print(f"[FAILED] Image {i+1} FAILED: {res.status_code}")

print(f"\n==================================")
print(f"TEST RUN COMPLETE: {success_count}/{total_count} PASSED")
print(f"==================================")
