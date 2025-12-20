import os
import socket
import random
import traceback
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp
import whisper

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
    Attempts to fetch captions directly from YouTube using youtube-transcript-api.
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([item['text'] for item in transcript_list])
        print(f"✅ Successfully obtained YouTube captions ({len(full_text)} chars)")
        return full_text
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"⚠️ YouTube captions not available: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Error fetching YouTube captions: {e}")
        return None

def apply_dns_patch():
    """
    Apply DNS patch to avoid connection issues.
    """
    try:
        # Simple DNS patch - can be extended if needed
        pass
    except:
        pass

def apply_user_agent_patch():
    """
    Apply user agent patch to avoid bot detection.
    """
    try:
        # User agent is set in yt-dlp options, so this is a placeholder
        pass
    except:
        pass

def get_transcript_from_notegpt(video_id):
    """
    Fallback method to fetch transcripts via NoteGPT API.
    Highly effective when YouTube blocks direct server requests.
    """
    import requests
    url = f"https://notegpt.io/api/v2/video-transcript?platform=youtube&video_id={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://notegpt.io/youtube-video-summarizer",
        "Origin": "https://notegpt.io"
    }
    
    print(f"🔍 [TIER 1.5] Attempting NoteGPT transcript fetch for: {video_id}")
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 200 and "data" in data:
                transcript_segments = data["data"].get("transcript", [])
                if transcript_segments:
                    full_text = " ".join([s.get("text", "") for s in transcript_segments])
                    print(f"✅ Successfully obtained transcript from NoteGPT ({len(full_text)} chars)")
                    return full_text
        print(f"⚠️ NoteGPT fetch failed with status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error fetching from NoteGPT: {e}")
    return None

def get_summary_from_notegpt(video_id):
    """
    Get video summary directly from NoteGPT API.
    This is the preferred method as it doesn't require cookies or downloads.
    """
    import requests
    url = f"https://notegpt.io/api/v2/video-summary?platform=youtube&video_id={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://notegpt.io/youtube-video-summarizer",
        "Origin": "https://notegpt.io",
        "Accept": "application/json"
    }
    
    print(f"📝 [NoteGPT] Attempting to get summary for video: {video_id}")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 200 and "data" in data:
                summary_data = data["data"]
                # Extract summary text - NoteGPT API structure may vary
                summary_text = summary_data.get("summary") or summary_data.get("text") or summary_data.get("content")
                if summary_text:
                    print(f"✅ Successfully obtained summary from NoteGPT ({len(summary_text)} chars)")
                    return summary_text
                # If structured summary exists
                if "points" in summary_data or "key_points" in summary_data:
                    points = summary_data.get("points") or summary_data.get("key_points", [])
                    if points:
                        summary_text = "\n".join([f"• {point}" if isinstance(point, str) else f"• {point.get('text', '')}" for point in points])
                        print(f"✅ Successfully obtained structured summary from NoteGPT")
                        return summary_text
        print(f"⚠️ NoteGPT summary fetch failed with status: {response.status_code}")
        # Try alternative endpoint
        return get_summary_from_notegpt_alt(video_id)
    except Exception as e:
        print(f"⚠️ Error fetching summary from NoteGPT: {e}")
        # Try alternative endpoint
        return get_summary_from_notegpt_alt(video_id)

def get_summary_from_notegpt_alt(video_id):
    """
    Alternative method: Get transcript and generate summary locally if NoteGPT summary API fails.
    """
    import requests
    # First try to get transcript
    transcript = get_transcript_from_notegpt(video_id)
    if transcript and len(transcript) > 50:
        # If we have transcript, try to get summary from a different endpoint
        url = f"https://notegpt.io/api/v2/summarize?platform=youtube&video_id={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://notegpt.io/youtube-video-summarizer",
            "Origin": "https://notegpt.io",
            "Accept": "application/json"
        }
        try:
            response = requests.post(url, headers=headers, json={"text": transcript[:5000]}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 200 and "data" in data:
                    summary = data["data"].get("summary") or data["data"].get("text")
                    if summary:
                        print(f"✅ Successfully obtained summary via alternative NoteGPT endpoint")
                        return summary
        except:
            pass
        # Fallback: return transcript as summary if no summary endpoint works
        print(f"⚠️ NoteGPT summary API not available, using transcript as summary")
        return transcript
    return None

def download_audio_with_ytdlp(video_url, outpath="temp_audio.mp3"):
    """
    Robust audio download using yt-dlp.
    NO COOKIES - STRICTLY GUEST MODE.
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
        'cookiefile': None,
        'cookiesfrombrowser': None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
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
        if "Sign in" in error_msg or "not a bot" in error_msg:
            raise Exception("NEEDS_AUTH")
        else:
            raise

def download_audio_with_ytdlp_with_cookies(video_url, cookies_path, outpath="temp_audio.mp3"):
    """
    Authenticated audio download using yt-dlp with cookies.
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
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': cookies_path,
    }
    
    if not cookies_path or not os.path.exists(cookies_path):
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
    Full entry point with multi-tier fallback strategy:
    1. Try YouTube API captions
    2. Try NoteGPT API fallback
    3. Try Guest Mode download (yt-dlp)
    4. Try Auth Mode download (cookies)
    """
    print(f"🎬 Processing video: {video_url} (ID: {video_id})")
    temp_audio = f"temp_{video_id if video_id else 'audio'}.mp3"
    
    if not video_id:
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]

    if video_id:
        # TIER 1: YouTube API
        print("📋 [TIER 1] Attempting to fetch YouTube captions via API...")
        caption_text = get_transcript_from_youtube_captions(video_id)
        if caption_text and len(caption_text) > 50:
            print("✅ Successfully obtained captions from YouTube API")
            return caption_text
        
        # TIER 2: NoteGPT
        print("📋 [TIER 2] YouTube API failed. Attempting NoteGPT fallback...")
        caption_text = get_transcript_from_notegpt(video_id)
        if caption_text and len(caption_text) > 50:
            print("✅ Successfully obtained transcript from NoteGPT")
            return caption_text

    # TIER 3: Guest Mode Download
    print("🔓 [TIER 3] Attempting download WITHOUT authentication...")
    try:
        audio_path = download_audio_with_ytdlp(video_url, outpath=temp_audio)
        text = transcribe_audio_file(audio_path)
        cleanup_temp_file(audio_path)
        return text
    except Exception as e:
        print(f"⚠️ Guest mode download failed: {e}")
        
    # TIER 4: Auth Mode Download
    print("🔑 [TIER 4] Attempting download WITH cookies...")
    try:
        audio_path = download_audio_with_ytdlp_with_cookies(video_url, cookies_path, temp_audio)
        text = transcribe_audio_file(audio_path)
        cleanup_temp_file(audio_path)
        return text
    except Exception as e:
        print(f"❌ Tier 4 failed: {e}")
        raise Exception("Failed to obtain transcription through any tier (API, NoteGPT, or Download).")
    finally:
        cleanup_temp_file(temp_audio)

def cleanup_temp_file(filepath):
    """Helper function to safely remove temporary files"""
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"🧹 Cleaned up temp file: {filepath}")
        except Exception as e:
            print(f"⚠️ Could not remove temp file {filepath}: {e}")