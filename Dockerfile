FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY docfinder/requirements.txt ./docfinder/
RUN pip install --no-cache-dir -r docfinder/requirements.txt
RUN pip install psutil uvicorn

# Copy all project files
COPY . .

# Setup environment variables
ENV BACKEND_URL=http://localhost:8000
# Render sets the PORT variable automatically, which frontend/server.py uses!

# Create a startup script that runs both backend and frontend
RUN echo '#!/bin/bash\n\
echo "Starting backend..."\n\
cd /app/docfinder && python -m uvicorn main:app --host 0.0.0.0 --port 8000 &\n\
sleep 5\n\
echo "Starting frontend..."\n\
cd /app/docfinder_frontend && python server.py\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

# Start both services
CMD ["/app/start.sh"]
