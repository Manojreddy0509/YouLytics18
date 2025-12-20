
import os
import yt_dlp
import whisper
import traceback
import socket
import random
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
    Applies a DNS monkey patch to resolve YouTube domains using a RANDOM working IP.
    This helps bypass 429 (Too Many Requests) by rotating destination IPs.
    """
    # Quick check: we ALWAYS want to check for new IPs on HF Spaces
    print("--- 🕵️ DNS Hunter (Randomized) ---")
    
    candidates = []
    # Domains to harvest IPs from
    domains = [
        'www.youtube.com', 
        'm.youtube.com', 
        'youtube.com', 
        'google.com', 
        'www.google.com'
    ]
    
    for domain in domains:
        try:
            # gethostbyname_ex returns (hostname, aliaslist, ipaddrlist)
            _, _, ips = socket.gethostbyname_ex(domain)
            for ip in ips:
                if ":" not in ip: # prefer IPv4 for compatibility
                    candidates.append(ip)
        except:
            continue
            
    # Add some known good Google IPs as backups
    candidates.extend(['142.250.190.46', '142.250.191.206', '172.217.204.206', '142.250.72.206'])
    
    working_ip = None
    if candidates:
        # De-duplicate
        candidates = list(set(candidates))
        working_ip = random.choice(candidates)
        print(f"🎲 Random IP selected from {len(candidates)} candidates: {working_ip}")
    
    if working_ip:
        if not getattr(socket, '_original_getaddrinfo', None):
            socket._original_getaddrinfo = socket.getaddrinfo

        def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            if host in ['www.youtube.com', 'm.youtube.com', 'youtube.com']:
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

def download_audio_with_ytdlp(video_url, outpath="temp_audio.mp3"):
    """
    Robust audio download using yt-dlp.
    NO COOKIES - STRICTLY GUEST MODE.
    
    Args:
        video_url: YouTube video URL
        outpath: Output path for audio file
    """
    # Ensure Network is patched before download
    apply_dns_patch()
    apply_user_agent_patch()
    
    print(f"⬇️ Starting download for: {video_url} (GUEST MODE / NO COOKIES)")

    # Prepare options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outpath.replace('.mp3', ''),
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0',
        # Use Android Client to mimic mobile app (often less strict)
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
            }
        },
        'referer': 'https://www.youtube.com/',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # Explicitly disable cookies
        'cookiefile': None,
        'cookiesfrombrowser': None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Check actual output filename
        if not os.path.exists(outpath):
            if os.path.exists(outpath + ".mp3"): 
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

def download_audio_with_ytdlp_with_cookies(video_url, cookies_path, outpath="temp_audio.mp3"):
    """
    Authenticated audio download using yt-dlp with cookies.
    Used as a fallback when guest access is blocked.
    """
    # Ensure Network is patched
    apply_dns_patch()
    apply_user_agent_patch()
    
    print(f"⬇️ Starting AUTHENTICATED download for: {video_url}")

    # Prepare options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outpath.replace('.mp3', ''),
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0',
        # Browser impersonation
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # COOKIES ENABLED
        'cookiefile': cookies_path,
    }
    
    # Validation
    if not cookies_path or not os.path.exists(cookies_path):
        # Fallback to env var if path invalid but env exists?
        if os.getenv("YOUTUBE_COOKIES"):
            print("🍪 Using cookies from Environment Variable YOUTUBE_COOKIES")
            with open("cookies_temp.txt", "w") as f:
                f.write(os.getenv("YOUTUBE_COOKIES"))
            ydl_opts['cookiefile'] = "cookies_temp.txt"
        else:
            raise Exception("Authentication required but no valid cookies found.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Check actual output filename
        if not os.path.exists(outpath):
            if os.path.exists(outpath + ".mp3"): 
                os.rename(outpath + ".mp3", outpath)
        
        if os.path.exists(outpath):
            print("✅ Authenticated audio download completed.")
            return outpath
        else:
             raise Exception("Output file not found after download.")
    
    except Exception as e:
        print(f"❌ Authenticated download failed: {e}")
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
    1. Try YouTube API captions (Guest Mode)
    2. Try downloading limit without cookies (Guest Mode)
    3. Try downloading WITH cookies (Auth Mode - Bypass for blocked IPs)
    4. Transcribe audio with Whisper
    5. Clean up temp files
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
    # TIER 2: Download Audio (GUEST MODE)
    # ═══════════════════════════════════════════════════════════
    print("🔓 [TIER 2] Attempting download WITHOUT authentication (public videos)...")
    
    try:
        # Download audio (Strictly Guest Mode now)
        audio_path = download_audio_with_ytdlp(video_url, outpath=temp_audio)
        
        # Transcribe
        print(f"🎤 Transcribing audio file: {audio_path}")
        text = transcribe_audio_file(audio_path)
        return text
            
    except Exception as e:
        print(f"❌ [TIER 2] Guest download failed: {e}")
        # Identify if it's an Auth error
        msg = str(e)
        if "Sign in" not in msg and "bot" not in msg and "429" not in msg:
             # Real error (not auth), try one more time or fail?
             pass 
    
    # ═══════════════════════════════════════════════════════════
    # TIER 3: Download Audio (AUTH MODE - COOKIES)
    # ═══════════════════════════════════════════════════════════
    print("🍪 [TIER 3] IP Blocked/Auth Required. Attempting download WITH cookies...")
    
    # Check if we actually have cookies
    if not cookies_path and not os.getenv("YOUTUBE_COOKIES"):
        print("❌ No cookies configured. Cannot proceed with Tier 3.")
        raise Exception("YouTube blocked guest access (Sign in required). Please configure COOKIES to bypass this.")

    try:
         # To use cookies, we need to pass them to yt-dlp. 
         # But wait, `download_audio_with_ytdlp` signature was simplified! 
         # I need to update THAT function too or handle it here.
         # I will update `download_audio_with_ytdlp` in the next step.
         # For now, I'll pass `cookiefile=cookies_path` assuming I will fix the callee.
         audio_path = download_audio_with_ytdlp_with_cookies(video_url, cookies_path, temp_audio) 
         
         text = transcribe_audio_file(audio_path)
         return text
         
    except Exception as e:
        print(f"❌ [TIER 3] Cookie download failed: {e}")
        raise Exception(f"Failed to transcribe (Cookies invalid?): {e}")

    finally:
        cleanup_temp_file(temp_audio)

def cleanup_temp_file(filepath):
    """Helper function to safely remove temporary files"""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"🧹 Cleaned up temp file: {filepath}")
        except Exception as e:
            print(f"⚠️ Could not remove temp file {filepath}: {e}")