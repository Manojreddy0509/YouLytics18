#!/bin/bash

# Start Redis in the background
echo "🟢 Starting Redis server..."
redis-server --daemonize yes

# Wait a moment for Redis to start
sleep 2

# Start Celery Worker in the background - logs will appear in container logs
echo "👷 Starting Celery worker..."
celery -A tasks.celery worker --loglevel=info -Q default -c 1 &

# Give Celery a moment to connect
sleep 3

# Start the Flask app (Gunicorn) in the foreground
echo "🚀 Starting Flask/Gunicorn..."
exec gunicorn app:app --bind 0.0.0.0:7860 --timeout 120 --workers 1
