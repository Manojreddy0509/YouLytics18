# Use an official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional, but useful for torch, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file first (to leverage Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# (Optional) explicitly install torch if not in requirements.txt
# RUN pip install torch==2.3.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy the rest of your code
COPY . .

# Debug check: ensure torch is installed
RUN python - <<EOF
import sys, importlib
print("python", sys.version.split()[0])
torch_ok = importlib.util.find_spec("torch") is not None
print("torch_installed=", torch_ok)
print("torch_version=", __import__("torch").__version__ if torch_ok else "none")
EOF

# Expose port (Render usually expects 10000 or $PORT)
EXPOSE 10000

# Start app (Render reads from Procfile, so keep it simple)
CMD ["sh", "-c", "echo 'Use Procfile for startup'"]


# Expose a safe local port and use $PORT at runtime (fallback 8000 for local dev)
EXPOSE 8000
CMD ["sh", "-c", "exec gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 1"]
