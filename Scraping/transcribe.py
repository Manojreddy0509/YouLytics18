# transcribe.py - FIXED VERSION
import os
import yt_dlp
import whisper
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use environment variable with fallback
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base").strip()

# Rest of your existing code...

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base").strip()
TEMP_AUDIO = "temp_audio.mp3"
TRANSCRIPTION_FILE = "transcription.txt"

# Optional yt-dlp config to handle restricted/403 videos
# - YTDLP_COOKIEFILE: path to a Netscape cookies.txt file
# - YTDLP_COOKIES_FROM_BROWSER: e.g. "chrome", "firefox", "safari" (requires browser profile access)
YTDLP_COOKIEFILE = os.getenv("YTDLP_COOKIEFILE", "").strip()
YTDLP_COOKIES_FROM_BROWSER = os.getenv("YTDLP_COOKIES_FROM_BROWSER", "").strip()

def download_audio_from_url(url: str) -> str:
    """
    Download best audio for a given URL (supports YouTube, etc.)
    Saves as temp_audio.mp3 in the current working directory.
    Returns path to downloaded audio file.
    """
    print(f"🎬 Downloading audio from: {url}")
    
    # If user provided a YouTube ID, build a YouTube url:
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        # Common YouTube hardening options (403/consent/age-gate often need one of these)
        'geo_bypass': True,
        'nocheckcertificate': True,
        # Prefer alternate client implementations if the default web player gets blocked
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        # Simulate a real browser
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        },
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
    }

    # Optional cookies (helps with 403/age-restricted/private videos)
    if YTDLP_COOKIEFILE:
        ydl_opts['cookiefile'] = YTDLP_COOKIEFILE
    if YTDLP_COOKIES_FROM_BROWSER:
        ydl_opts['cookiesfrombrowser'] = (YTDLP_COOKIES_FROM_BROWSER,)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("⬇️ Starting download...")
            ydl.download([url])
        print("✅ Audio download completed")
        return TEMP_AUDIO
    except Exception as e:
        print(f"❌ Audio download failed: {e}")
        # Try alternative approach
        return download_audio_alternative(url)

def download_audio_alternative(url: str) -> str:
    """
    Alternative download method with different options
    """
    print("🔄 Trying alternative download method...")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'geo_bypass': True,
        'nocheckcertificate': True,
        # Simulate a browser more effectively
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'extract_flat': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
    }

    if YTDLP_COOKIEFILE:
        ydl_opts['cookiefile'] = YTDLP_COOKIEFILE
    if YTDLP_COOKIES_FROM_BROWSER:
        ydl_opts['cookiesfrombrowser'] = (YTDLP_COOKIES_FROM_BROWSER,)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Alternative download completed")
        return TEMP_AUDIO
    except Exception as e:
        print(f"❌ Alternative download also failed: {e}")
        raise Exception(f"Could not download video: {str(e)}")

def transcribe_and_translate_to_english(audio_path: str, whisper_model_size: str = WHISPER_MODEL_SIZE) -> str:
    """
    Uses OpenAI Whisper (python package) to transcribe and translate to English.
    Returns the English text string and also writes it to transcription.txt.
    """
    print(f"🔊 Loading Whisper model: {whisper_model_size}")
    try:
        model = whisper.load_model(whisper_model_size)
        print("✅ Whisper model loaded successfully")
        
        print("🎤 Starting transcription...")
        # Use task="translate" to ensure output is in English if original language differs.
        result = model.transcribe(audio_path, task="translate", fp16=False)
        text = result.get("text", "").strip()
        
        print(f"✅ Transcription completed: {len(text)} characters")
        
        # Save to file
        with open(TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"💾 Transcription saved to: {TRANSCRIPTION_FILE}")
        
        return text
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        print(f"Debug info: {traceback.format_exc()}")
        raise

def cleanup_temp_audio():
    if os.path.exists(TEMP_AUDIO):
        try:
            os.remove(TEMP_AUDIO)
            print("🧹 Temporary audio file cleaned up")
        except Exception as e:
            print(f"⚠️ Could not remove temp audio file: {e}")

def transcribe_video_or_url(source: str) -> str:
    """
    Top-level convenience function:
    - if source is a local file path and exists -> transcribe local file
    - else treat as URL/YouTube ID -> download audio then transcribe
    Returns transcribed (English) text.
    """
    print(f"🎯 Starting transcription for: {source}")
    
    # If it's a local file that exists, use it directly with whisper
    if os.path.exists(source):
        print("📁 Using local file")
        audio_path = source
        cleanup_needed = False
    else:
        print("🌐 Downloading from URL")
        audio_path = download_audio_from_url(source)
        cleanup_needed = True

    try:
        text = transcribe_and_translate_to_english(audio_path)
        return text
    except Exception as e:
        print(f"❌ Transcription process failed: {e}")
        return f"Transcription failed: {str(e)}\n\nPlease try a different YouTube video or check if the video is available."
    finally:
        # If we downloaded to temp_audio.mp3, remove it
        if cleanup_needed and audio_path == TEMP_AUDIO:
            cleanup_temp_audio()