
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

def apply_user_agent_patch():
    """
    Patches requests.Session.request to ensure a browser-like User-Agent
    defaults on all outgoing requests. This helps bypass simple bot checks.
    """
    import requests
    
    # Check if already patched
    if getattr(requests.Session, '_patched_for_ua', False):
        return

    _original_request = requests.Session.request
    
    def patched_request(self, method, url, *args, **kwargs):
        # Default Headers mimicking Chrome on macOS
        headers = kwargs.get('headers', {})
        if not headers:
            headers = {}
        
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        kwargs['headers'] = headers
        return _original_request(self, method, url, *args, **kwargs)

    requests.Session.request = patched_request
    requests.Session._patched_for_ua = True
    print("🎭 User-Agent Patch applied to requests.")

def apply_dns_patch():
    """
    Applies a DNS monkey patch to resolve YouTube domains using a working IP.
    This fixes specific container DNS resolution errors.
    """
    # Quick check to see if we need it
    try:
        socket.gethostbyname('www.youtube.com')
        return  # DNS is working fine
    except:
        pass
        
    print("--- 🕵️ DNS Hunter (Global Patch) ---")
    working_ip = None
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
        print(f"💉 DNS Monkey Patch applied globally: {working_ip}")

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
    Uses list_transcripts for better robustness.
    """
    # Ensure Network is patched before API call
    apply_dns_patch()
    apply_user_agent_patch()
    
    print(f"🔍 Checking for YouTube captions for ID: {video_id}")
    
    try:
        # fetch lists of transcripts - NO cookies used to avoid bot detection with expired auth
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript = None
        
        # 1. Try manually created English
        try:
            transcript = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
            print("✅ Found manually created English captions.")
        except:
            pass
            
        # 2. Try auto-generated English
        if not transcript:
            try:
                transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
                print("✅ Found auto-generated English captions.")
            except:
                pass
                
        # 3. Fallback: Any English-ish transcript?
        if not transcript:
             for t in transcript_list:
                if t.language_code.startswith('en'):
                    transcript = t
                    print(f"✅ Found English caption track: {t.language_code}")
                    break
        
        # 4. Fallback: Translate whatever exists to English
        if not transcript:
            try:
                # Get the first available transcript and translate it
                first_transcript = next(iter(transcript_list))
                if first_transcript.is_translatable:
                    transcript = first_transcript.translate('en')
                    print(f"✅ Translating captions from {first_transcript.language_code} to English.")
            except:
                pass

        if transcript:
            full_text = " ".join([t['text'] for t in transcript.fetch()])
            return full_text
        
        print("⚠️ No suitable captions found.")
        return None
        
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"⚠️ No captions found/disabled: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Error fetching captions: {e}")
        return None

def download_audio_with_ytdlp(video_url, use_cookies=True, cookiefile=None, outpath="temp_audio.mp3"):
    """
    Robust audio download using yt-dlp.
    Handles DNS patching and cookie file usage logic internally.
    
    Args:
        video_url: YouTube video URL
        use_cookies: If True, attempt to use cookies. If False, skip cookies entirely.
        cookiefile: Path to cookie file (optional)
        outpath: Output path for audio file
    """
    # Ensure Network is patched before download
    apply_dns_patch()
    apply_user_agent_patch()
    
    cookie_mode = "with cookies" if use_cookies else "WITHOUT cookies"
    print(f"⬇️ Starting download for: {video_url} ({cookie_mode})")

    # Prepare options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outpath.replace('.mp3', ''),  # yt-dlp adds extension based on postprocessor
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0',
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    # Handle Cookies - Only if use_cookies=True
    if use_cookies:
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
        else:
            print("⚠️ Cookies requested but none found")
    else:
        print("🔓 Attempting download without authentication")

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
        error_msg = str(e)
        print(f"❌ Download failed: {error_msg}")
        
        # Return specific error type for better handling upstream
        if "Sign in" in error_msg or "not a bot" in error_msg:
            raise Exception("NEEDS_AUTH")
        elif "Private video" in error_msg:
            raise Exception("This video is private and cannot be accessed.")
        elif "Video unavailable" in error_msg:
            raise Exception("This video is unavailable or has been removed.")
        else:
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
    Main entry point with robust multi-tier fallback strategy:
    1. Try YouTube API captions (fastest, no auth)
    2. Try downloading without cookies (works for public videos)
    3. Try downloading with cookies (if cookies are available)
    4. Transcribe audio with Whisper
    5. Clean up temp files
    
    Returns: transcript text
    Raises: Exception with user-friendly error message if all methods fail
    """
    print(f"🎬 Processing video: {video_url} (ID: {video_id})")
    temp_audio = f"temp_{video_id if video_id else 'audio'}.mp3"
    
    # ═══════════════════════════════════════════════════════════
    # TIER 1: Try YouTube API Captions (No Download Needed)
    # ═══════════════════════════════════════════════════════════
    if video_id:
        print("📋 [TIER 1] Attempting to fetch YouTube captions via API...")
        caption_text = get_transcript_from_youtube_captions(video_id)
        if caption_text and len(caption_text) > 50:
            print("✅ Successfully obtained captions from YouTube API")
            return caption_text
        print("⚠️ No suitable captions found, proceeding to audio download...")
    
    # ═══════════════════════════════════════════════════════════
    # TIER 2: Try Download WITHOUT Cookies (Public Videos)
    # ═══════════════════════════════════════════════════════════
    print("🔓 [TIER 2] Attempting download WITHOUT authentication (public videos)...")
    try:
        audio_path = download_audio_with_ytdlp(
            video_url, 
            use_cookies=False,  # Don't use cookies
            outpath=temp_audio
        )
        print("✅ Download succeeded without authentication!")
        try:
            text = transcribe_audio_file(audio_path)
            return text
        finally:
            cleanup_temp_file(temp_audio)
    
    except Exception as e:
        error_msg = str(e)
        
        # If it's not an auth issue, this is a real error
        if error_msg != "NEEDS_AUTH":
            print(f"❌ Download failed with error: {error_msg}")
            cleanup_temp_file(temp_audio)
            raise Exception(f"Unable to download video: {error_msg}")
        
        # Auth required - try with cookies
        print("🔐 Video requires authentication, attempting with cookies...")
    
    # ═══════════════════════════════════════════════════════════
    # TIER 3: Try Download WITH Cookies (Restricted Videos)
    # ═══════════════════════════════════════════════════════════
    print("🍪 [TIER 3] Attempting download WITH cookies...")
    
    # Check if cookies are available
    has_cookies = (
        cookies_path and os.path.exists(cookies_path)
    ) or os.getenv("YOUTUBE_COOKIES") or os.getenv("YTDLP_COOKIEFILE")
    
    if not has_cookies:
        cleanup_temp_file(temp_audio)
        raise Exception(
            "This video requires authentication, but no cookies are configured. "
            "Please add YouTube cookies to access age-restricted or members-only content. "
            "See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"
        )
    
    try:
        audio_path = download_audio_with_ytdlp(
            video_url,
            use_cookies=True,
            cookiefile=cookies_path,
            outpath=temp_audio
        )
        print("✅ Download succeeded with cookie authentication!")
        try:
            text = transcribe_audio_file(audio_path)
            return text
        finally:
            cleanup_temp_file(temp_audio)
    
    except Exception as e:
        error_msg = str(e)
        cleanup_temp_file(temp_audio)
        
        # Provide helpful error message
        if error_msg == "NEEDS_AUTH":
            raise Exception(
                "Cookie authentication failed - your cookies may be expired or invalid. "
                "Please update your YouTube cookies. "
                "See: https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies"
            )
        else:
            raise Exception(f"Video download failed: {error_msg}")

def cleanup_temp_file(filepath):
    """Helper function to safely remove temporary files"""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"🧹 Cleaned up temp file: {filepath}")
        except Exception as e:
            print(f"⚠️ Could not remove temp file {filepath}: {e}")