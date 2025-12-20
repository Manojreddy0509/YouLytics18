import os
import traceback
import socket
import random
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Load environment variables
load_dotenv()

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
        # TIER 1: Try fetching transcripts via API
        # Handle different library versions by checking for class methods vs instance methods
        api = YouTubeTranscriptApi()
        
        try:
            # Try instance fetch (v1.2.x style) or class method get_transcript (v0.6.x style)
            if hasattr(api, 'fetch'):
                transcript_data = api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
            elif hasattr(YouTubeTranscriptApi, 'get_transcript'):
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
            else:
                transcript_data = None

            if transcript_data:
                # TD is iterable. We need to handle both dicts and objects for snippets.
                segments = list(transcript_data.fetch()) if hasattr(transcript_data, 'fetch') else transcript_data
                
                parts = []
                for s in segments:
                    if isinstance(s, dict):
                        parts.append(s.get('text', ''))
                    else:
                        parts.append(getattr(s, 'text', ''))
                
                full_text = " ".join(parts).strip()
                if full_text:
                    print("✅ Successfully obtained captions from YouTube API")
                    return full_text
        except Exception as e:
            print(f"⚠️ Direct caption fetch failed: {e}")

        try:
            # Fallback to listing transcripts
            if hasattr(api, 'list'):
                transcript_list = api.list(video_id)
            elif hasattr(YouTubeTranscriptApi, 'list_transcripts'):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            else:
                 return None
            
            transcript = None
            
            # 1. Try manually created English
            try:
                transcript = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
            except:
                pass
                
            # 2. Try auto-generated English
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
                except:
                    pass
            
            if transcript:
                segments = list(transcript.fetch())
                parts = []
                for s in segments:
                    if isinstance(s, dict):
                        parts.append(s.get('text', ''))
                    else:
                        parts.append(getattr(s, 'text', ''))
                
                full_text = " ".join(parts).strip()
                return full_text
        except Exception as inner_e:
            print(f"⚠️ List transcripts failed: {inner_e}")
            
        return None
        
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"⚠️ No captions found/disabled: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Error fetching captions: {e}")
        return None

def transcribe_audio_from_video(video_url, video_id=None, cookies_path=None):
    """
    Main entry point for transcription.
    Exclusively uses API-based methods to ensure cloud reliability:
    1. Try YouTube API Captions
    2. Fallback to NoteGPT API
    """
    print(f"🎬 Processing video: {video_url} (ID: {video_id})")
    
    if not video_id:
        print("⚠️ No video ID provided, attempting to extract from URL.")
        # Minimal extraction if needed, but usually video_id is passed
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]

    if video_id:
        # ═══════════════════════════════════════════════════════════
        # TIER 1: Try YouTube API Captions
        # ═══════════════════════════════════════════════════════════
        print("📋 [TIER 1] Attempting to fetch YouTube captions via API...")
        caption_text = get_transcript_from_youtube_captions(video_id)
        if caption_text and len(caption_text) > 50:
            print("✅ Successfully obtained captions from YouTube API")
            return caption_text
        
        # ═══════════════════════════════════════════════════════════
        # TIER 2: NoteGPT API Fallback (High Reliability)
        # ═══════════════════════════════════════════════════════════
        print("📋 [TIER 2] YouTube API failed. Attempting NoteGPT fallback...")
        caption_text = get_transcript_from_notegpt(video_id)
        if caption_text and len(caption_text) > 50:
            print("✅ Successfully obtained transcript from NoteGPT")
            return caption_text

    raise Exception("Could not obtain transcription from YouTube API or NoteGPT fallback.")