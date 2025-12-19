
import os
from celery import Celery
from celery.signals import worker_process_init
from Scraping.transcribe import transcribe_audio_from_video, init_whisper
from Summarise.summarize import summarize_text, init_summarizer

# Redis Configuration (Defaults for localhost, but likely overridden in prod)
# IMPORTANT: For Hugging Face Spaces, you might need a managed Redis URL via env var.
BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
BACKEND_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

celery = Celery('tasks', broker=BROKER_URL, backend=BACKEND_URL)

@worker_process_init.connect
def init_worker(**kwargs):
    """
    Load models once when the worker process starts.
    This saves massive overhead per task.
    """
    print("👷 Worker process initializing...")
    try:
        init_whisper("base")
        init_summarizer()
        print("✅ Models initialized in worker process.")
    except Exception as e:
        print(f"❌ Failed to initialize models in worker: {e}")

@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def transcribe_and_summarize(self, video_url, video_id=None, cookies_path=None):
    """
    Main background task.
    """
    print(f"🚀 Task started for: {video_url}")
    try:
        # 1. Transcribe (Captions or Download -> Whisper)
        # Note: We don't pass cookies_path directly if it's strictly file based, 
        # but transcribe_audio_from_video handles env vars internally too.
        transcript = transcribe_audio_from_video(video_url, video_id, cookies_path)
        
        # 2. Summarize
        summary = summarize_text(transcript)
        
        return {
            "status": "ok",
            "summary": summary,
            "text_len": len(transcript)
        }
        
    except Exception as exc:
        print(f"❌ Task failed: {exc}")
        # Retry for network glitches, but maybe not for Auth errors?
        # For now, simplistic retry:
        raise self.retry(exc=exc)
