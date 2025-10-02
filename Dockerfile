# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Copy requirements.txt first (for caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of your app
COPY . /app

# Expose default local port
EXPOSE 8000

# Use Render's $PORT with fallback for local dev
CMD ["sh", "-c", "exec gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 1"]



