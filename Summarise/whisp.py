# transcribe.py
import os
import yt_dlp
import whisper

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base").strip()
TEMP_AUDIO = "temp_audio.mp3"
TRANSCRIPTION_FILE = "transcription.txt"

def download_audio_from_url(url: str) -> str:
    """
    Download best audio for a given URL (supports YouTube, etc.)
    Saves as temp_audio.mp3 in the current working directory.
    Returns path to downloaded audio file.
    """
    # If user provided a YouTube ID, build a YouTube url:
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    # temp_audio.mp3 should exist now
    return TEMP_AUDIO

def transcribe_and_translate_to_english(audio_path: str, whisper_model_size: str = WHISPER_MODEL_SIZE):
    """
    Uses OpenAI Whisper (python package) to transcribe and translate to English.
    Returns the English text string and segments.
    """
    model = whisper.load_model(whisper_model_size)
    # Use task="translate" to ensure output is in English if original language differs.
    result = model.transcribe(audio_path, task="translate", fp16=False)
    text = result.get("text", "").strip()
    segments = result.get("segments", [])
    
    # Save to file
    with open(TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    return text, segments

def cleanup_temp_audio():
    if os.path.exists(TEMP_AUDIO):
        try:
            os.remove(TEMP_AUDIO)
        except Exception:
            pass

def transcribe_video_or_url(source: str):
    """
    Top-level convenience function:
    - 1. Try fetching existing YouTube transcript (FAST)
    - 2. If local file -> transcribe
    - 3. If URL -> download audio -> transcribe (SLOW)
    Returns transcribed (English) text and segments.
    """
    
    # Strategy 1: Check for existing transcript first (if it looks like a URL/ID)
    if not os.path.exists(source):
        text, segments = get_transcript_if_available(source)
        if text and segments:
            return text, segments

    # Strategy 2: Fallback to Whisper (Download + Transcribe)
    # If it's a local file that exists, use it directly with whisper
    if os.path.exists(source):
        audio_path = source
    else:
        audio_path = download_audio_from_url(source)

    try:
        text, segments = transcribe_and_translate_to_english(audio_path)
    finally:
        # If we downloaded to temp_audio.mp3, remove it
        if audio_path == TEMP_AUDIO:
            cleanup_temp_audio()
    return text, segments
