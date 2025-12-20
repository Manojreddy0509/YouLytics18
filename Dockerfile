FROM python:3.11-slim

# System deps: ffmpeg for audio extraction, plus minimal build tools for some wheels
# System deps: ffmpeg for audio processing, git, nodejs for yt-dlp js execution, and redis-server
RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg git redis-server nodejs \
  && ( [ -e /usr/bin/node ] || ln -s /usr/bin/nodejs /usr/bin/node ) \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Make startup script executable
RUN chmod +x start.sh

ENV TOKENIZERS_PARALLELISM=false

# Hugging Face Spaces (Docker) expects the app to listen on port 7860
# Use start.sh to launch Redis + Celery + Gunicorn
CMD ["bash", "start.sh"]
