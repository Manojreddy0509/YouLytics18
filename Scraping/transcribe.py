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

    # Try different client configurations to avoid bot detection
    clients = [
        ['android', 'ios', 'web'],
        ['web', 'android'],
        ['mweb', 'android'],
        ['tv', 'web']
    ]

    # --- DNS MONKEY PATCH ---
    # This is necessary because the hosting environment fails to resolve www.youtube.com
    import socket
    
    # 1. Find a working IP from accessible Google domains
    working_ip = None
    print("--- 🕵️ DNS Hunter ---")
    for domain in ['youtube.com', 'm.youtube.com', 'google.com', 'youtube.googleapis.com']:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ Found working IP from {domain}: {ip}")
            working_ip = ip
            break
        except:
            continue
    
    if working_ip:
        print(f"🎯 Locking target IP: {working_ip}")
        # Monkey Patch socket.getaddrinfo
        if not getattr(socket, '_original_getaddrinfo', None):
            socket._original_getaddrinfo = socket.getaddrinfo

        def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            # Intercept www.youtube.com AND m.youtube.com
            if host in ['www.youtube.com', 'm.youtube.com']:
                return socket._original_getaddrinfo(working_ip, port, family, type, proto, flags)
            return socket._original_getaddrinfo(host, port, family, type, proto, flags)

        socket.getaddrinfo = patched_getaddrinfo
        print("💉 DNS Monkey Patch applied successfully.")
    print("----------------------")

    # Initialize cookie file variable
    YTDLP_COOKIEFILE = None

    # Check for YOUTUBE_COOKIES env var (optional, but recommended if 429/403 errors occur)
    if os.getenv("YOUTUBE_COOKIES"):
        print("🍪 Cookies detected in environment.")
        with open("cookies.txt", "w") as f:
            f.write(os.getenv("YOUTUBE_COOKIES"))
        YTDLP_COOKIEFILE = "cookies.txt"
    # Fallback to global env var if set
    elif os.getenv("YTDLP_COOKIEFILE"):
         YTDLP_COOKIEFILE = os.getenv("YTDLP_COOKIEFILE")

    # Simplified, robust extraction options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        # Use IPv4 source address to avoid IPv6 blocks
        'source_address': '0.0.0.0', 
        # Use a mobile client which is often less restricted
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
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

    if YTDLP_COOKIEFILE and os.path.exists(YTDLP_COOKIEFILE):
        ydl_opts['cookiefile'] = YTDLP_COOKIEFILE

    try:
        print(f"⬇️ Starting download for: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Audio download completed successfully!")
        return TEMP_AUDIO
    except Exception as e:
        print(f"❌ Download failed: {e}")
        raise Exception(f"Video download failed. The server might be blocked by YouTube. Error: {str(e)}")

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