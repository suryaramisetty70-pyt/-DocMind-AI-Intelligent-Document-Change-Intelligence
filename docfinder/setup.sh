#!/bin/bash
# DocFinder Setup Script for Render

echo "🔧 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies installed!"

echo "🚀 Starting DocFinder..."
uvicorn main:app --host 0.0.0.0 --port $PORT
