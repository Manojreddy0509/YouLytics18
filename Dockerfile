FROM python:3.11-slim

# System deps: ffmpeg for audio extraction, plus minimal build tools for some wheels
RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg git \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

ENV TOKENIZERS_PARALLELISM=false

# Render/Heroku-style platforms provide $PORT
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5001}
