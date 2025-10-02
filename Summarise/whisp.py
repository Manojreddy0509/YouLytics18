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

def transcribe_and_translate_to_english(audio_path: str, whisper_model_size: str = WHISPER_MODEL_SIZE) -> str:
    """
    Uses OpenAI Whisper (python package) to transcribe and translate to English.
    Returns the English text string and also writes it to transcription.txt.
    """
    model = whisper.load_model(whisper_model_size)
    # Use task="translate" to ensure output is in English if original language differs.
    result = model.transcribe(audio_path, task="translate", fp16=False)
    text = result.get("text", "").strip()
    # Save to file
    with open(TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    return text

def cleanup_temp_audio():
    if os.path.exists(TEMP_AUDIO):
        try:
            os.remove(TEMP_AUDIO)
        except Exception:
            pass

def transcribe_video_or_url(source: str) -> str:
    """
    Top-level convenience function:
    - if source is a local file path and exists -> transcribe local file
    - else treat as URL/YouTube ID -> download audio then transcribe
    Returns transcribed (English) text.
    """
    # If it's a local file that exists, use it directly with whisper
    if os.path.exists(source):
        audio_path = source
    else:
        audio_path = download_audio_from_url(source)

    try:
        text = transcribe_and_translate_to_english(audio_path)
    finally:
        # If we downloaded to temp_audio.mp3, remove it
        if audio_path == TEMP_AUDIO:
            cleanup_temp_audio()
    return text
