# Dockerfile (place in repo root)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System deps (ffmpeg + libs whisper may need)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg libsndfile1 build-essential git && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements (we'll install torch separately)
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install CPU-only torch from PyTorch CPU index
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.1+cpu

# Install remaining Python packages (requirements.txt should NOT include torch)
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy app code
COPY . /app

EXPOSE 5000

# Start with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "1"]
