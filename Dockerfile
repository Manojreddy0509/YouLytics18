# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ffmpeg \
        curl \
        build-essential \
        libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first for caching
COPY requirements.txt /app/requirements.txt

# Upgrade pip and setuptools
RUN python -m pip install --upgrade pip setuptools wheel

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of your app
COPY . /app

# Expose the port Render uses
EXPOSE 5000

# Command to run your Flask app with Gunicorn
# Render sets $PORT automatically
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT", "--workers", "1"]

