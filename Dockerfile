# -----------------
# Base image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies (needed for lxml, spacy, pdfplumber)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

# Expose port
EXPOSE 8000

# Default command: gunicorn with uvicorn workers
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "backend.main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]

