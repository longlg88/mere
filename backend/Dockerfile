FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy legacy backend files for compatibility
COPY backend/Dockerfile ./

# Set Python path to include src directory  
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Expose port
EXPOSE 8000

# Run the application from new structure
CMD ["uvicorn", "mere.api.main:app", "--host", "0.0.0.0", "--port", "8000"]