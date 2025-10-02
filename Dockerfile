# Use official Python image (slim version for smaller size)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only dependency files first for better caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip setuptools wheel

# Install PyTorch CPU version (latest working build) + other requirements
RUN python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.2+cpu \
    torchvision==0.16.2+cpu \
    torchaudio==2.1.2+cpu

# Install other Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Expose port if your app runs a server
EXPOSE 5000

# Default command to run your app
# Replace app.py with your entry point script
CMD ["python", "app.py"]

