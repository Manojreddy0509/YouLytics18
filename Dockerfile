# Dockerfile — stable for Whisper + Torch + Flask on Python 3.11
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# system dependencies (ffmpeg needed by whisper), minimal tools for building wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git \
      ffmpeg \
      libsndfile1 \
      build-essential \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# copy requirements for caching
COPY requirements.txt /app/requirements.txt

# upgrade pip + install numpy<2 (avoid numpy v2 issues)
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir "numpy<2.0"

# Install Whisper first (it will pull a compatible torch) and pandas (if you need it)
# --prefer-binary helps pip pick prebuilt wheels where available
RUN python -m pip install --no-cache-dir --prefer-binary git+https://github.com/openai/whisper.git pandas

# Now install the rest of your requirements (requirements.txt MUST NOT contain torch/torchaudio/torchvision)
RUN python -m pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

# copy app code
COPY . /app

# health / port
EXPOSE 5000

# Use Gunicorn; Render/other hosts set $PORT
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT", "--workers", "1"]


