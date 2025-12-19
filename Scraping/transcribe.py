
import os
import yt_dlp
import whisper
import traceback
import socket
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Load environment variables
load_dotenv()

# Global variable for the Whisper model (loaded once per process)
WHISPER_MODEL = None

def init_whisper(model_name="base"):
    """
    Loads the Whisper model into the global variable WHISPER_MODEL.
    Should be called once at worker startup.
    """
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        print(f"🔊 Loading Whisper model: {model_name}...")
        try:
            WHISPER_MODEL = whisper.load_model(model_name)
            print("✅ Whisper model loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load Whisper model: {e}")
            raise

def get_transcript_from_youtube_captions(video_id):
    """
    Tries to fetch transcripts using youtube_transcript_api.
    Returns the transcript string or None if not found.
    """
    print(f"🔍 Checking for YouTube captions for ID: {video_id}")
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        # transcript_list is a list of dicts: {'text': '...', 'start': ...}
        full_text = " ".join([t['text'] for t in transcript_list])
        print("✅ Found YouTube captions.")
        return full_text
    except (TranscriptsDisabled, NoTranscriptFound):
        print("⚠️ No captions found/disabled.")
        return None
    except Exception as e:
        print(f"⚠️ Error fetching captions: {e}")
        return None

def download_audio_with_ytdlp(video_url, cookiefile=None, outpath="temp_audio.mp3"):
    """
    Robust audio download using yt-dlp.
    Handles DNS patching and cookie file usage logic internally.
    """
    print(f"⬇️ Starting download for: {video_url}")
    
    # --- DNS MONKEY PATCH (Retained from previous fix) ---
    working_ip = None
    # Quick check to see if we need it
    try:
        socket.gethostbyname('www.youtube.com')
    except:
        print("--- 🕵️ DNS Hunter (Fallback) ---")
        for domain in ['youtube.com', 'm.youtube.com', 'google.com']:
            try:
                ip = socket.gethostbyname(domain)
                working_ip = ip
                break
            except:
                continue
        
        if working_ip:
            if not getattr(socket, '_original_getaddrinfo', None):
                socket._original_getaddrinfo = socket.getaddrinfo

            def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
                if host in ['www.youtube.com', 'm.youtube.com']:
                    return socket._original_getaddrinfo(working_ip, port, family, type, proto, flags)
                return socket._original_getaddrinfo(host, port, family, type, proto, flags)

            socket.getaddrinfo = patched_getaddrinfo
            print(f"💉 DNS Monkey Patch applied: {working_ip}")

    # Prepare options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outpath.replace('.mp3', ''),  # yt-dlp adds extension based on postprocessor
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    # Handle Cookies
    # 1. Passed argument (highest priority)
    # 2. Env var content (YOUTUBE_COOKIES) written to file
    # 3. Env var pointer (YTDLP_COOKIEFILE)
    
    final_cookiefile = None
    if cookiefile and os.path.exists(cookiefile):
        final_cookiefile = cookiefile
    elif os.getenv("YOUTUBE_COOKIES"):
        # Create temp cookie file from env var
        with open("cookies.txt", "w") as f:
            f.write(os.getenv("YOUTUBE_COOKIES"))
        final_cookiefile = "cookies.txt"
    elif os.getenv("YTDLP_COOKIEFILE"):
        final_cookiefile = os.getenv("YTDLP_COOKIEFILE")

    if final_cookiefile:
        print(f"🍪 Using cookies from: {final_cookiefile}")
        ydl_opts['cookiefile'] = final_cookiefile

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Check actual output filename
        possible_out = outpath
        if not os.path.exists(possible_out):
            # sometimes yt-dlp naming varies, but outtmpl should handle it mostly.
            # verify simply:
            if os.path.exists(outpath + ".mp3"): # edge case
                os.rename(outpath + ".mp3", outpath)
        
        if os.path.exists(outpath):
            print("✅ Audio download completed.")
            return outpath
        else:
             raise Exception("Output file not found after download.")

    except Exception as e:
        print(f"❌ Download failed: {e}")
        msg = str(e)
        if "Sign in" in msg or "cookies" in msg:
            raise Exception("YouTube requires authentication (Cookies). Please configure YOUTUBE_COOKIES.")
        raise

def transcribe_audio_file(audio_file_path):
    """
    Transcribes a local audio file using the global Whisper model.
    """
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        # Fallback for direct usage, though init_whisper is preferred
        init_whisper()
    
    print(f"🎤 Transcribing audio file: {audio_file_path}")
    try:
        result = WHISPER_MODEL.transcribe(audio_file_path, task="translate", fp16=False)
        text = result.get("text", "").strip()
        print(f"✅ Transcription completed: {len(text)} chars")
        return text
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        raise

def transcribe_audio_from_video(video_url, video_id=None, cookies_path=None):
    """
    Main entry point:
    1. Try captions (fastest).
    2. If no captions, download audio with yt-dlp.
    3. Transcribe audio.
    4. Clean up.
    Returns: transcript text.
    """
    print(f"🎬 Processing video: {video_url} (ID: {video_id})")
    
    # 1. Try Captions
    if video_id:
        text = get_transcript_from_youtube_captions(video_id)
        if text and len(text) > 50:
            return text
    
    # 2. Download & Transcribe
    temp_audio = f"temp_{video_id if video_id else 'audio'}.mp3"
    try:
        audio_path = download_audio_with_ytdlp(video_url, cookiefile=cookies_path, outpath=temp_audio)
        text = transcribe_audio_file(audio_path)
        return text
    finally:
        # 4. Clean up
        if os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
                print("🧹 Temp file cleaned.")
            except:
                pass