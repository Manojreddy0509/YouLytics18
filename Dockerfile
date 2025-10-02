# Dockerfile — Render-ready, ensures torch is installed (CPU)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git ffmpeg libsndfile1 build-essential ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements for caching
COPY requirements.txt /app/requirements.txt

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Lock numpy to <2.0 to avoid torch/NumPy 2.0 incompatibilities
RUN python -m pip install --no-cache-dir "numpy<2.0"

# Install PyTorch CPU wheels explicitly first (so it's available at runtime)
# Use the PyTorch CPU index. Using --prefer-binary helps pick prebuilt wheels.
RUN python -m pip install --no-cache-dir --prefer-binary \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch" "torchvision" "torchaudio"

# Now install the rest of your Python deps (whisper/transformers, etc.)
# Whisper from GitHub will use the torch already installed.
RUN python -m pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

# Copy app code
COPY . /app

# Sanity checks that will show in build logs (optional but useful)
RUN python -c "import sys, importlib; \
    print('python', sys.version.split()[0]); \
    torch_ok = importlib.util.find_spec('torch') is not None; \
    print('torch_installed=', torch_ok); \
    import pkgutil; \
    print('torch_version=', __import__('torch').__version__ if torch_ok else 'none')"

# Expose a safe local port and use $PORT at runtime (fallback 8000 for local dev)
EXPOSE 8000
CMD ["sh", "-c", "exec gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 1"]
