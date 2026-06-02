# DocMind AI Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OCR and document processing
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-tel \
    tesseract-ocr-hin \
    tesseract-ocr-tam \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY docmind_ai/ ./docmind_ai/
COPY ui/ ./ui/
COPY docs/ ./docs/

# Create data directories
RUN mkdir -p data/uploads data/processed data/reports

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV DATABASE_URL=sqlite:///./docmind.db

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Default command - run both API and UI
CMD ["sh", "-c", "uvicorn docmind_ai.api.app:app --host 0.0.0.0 --port 8000 & streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0"]