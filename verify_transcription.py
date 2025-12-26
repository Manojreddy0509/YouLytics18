import sys
import os
import traceback

# Add the current directory to sys.path so we can import Scraping
sys.path.append(os.getcwd())

from Scraping.whisper_transcribe import transcribe_youtube

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_transcription.py <youtube_url> [video_id]")
        sys.exit(1)

    video_url = sys.argv[1]
    video_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Try to extract video ID if not provided
    if not video_id:
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be" in video_url:
            video_id = video_url.split("/")[-1]

    print(f"🚀 Starting verification for: {video_url}")
    print(f"🆔 Video ID: {video_id}")
    
    try:
        print("🎬 Running transcribe_youtube...")
        transcript = transcribe_youtube(video_url)
        
        if transcript:
            print("\n" + "="*50)
            print("✅ SUCCESS!")
            print(f"Length: {len(transcript)} characters")
            print(f"Preview:\n{transcript[:500]}...")
            print("="*50)
        else:
            print("\n" + "x"*50)
            print("❌ FAILED: No transcript returned.")
            print("x"*50)
            
    except Exception as e:
        print("\n" + "x"*50)
        print(f"💥 CRITICAL ERROR: {e}")
        traceback.print_exc()
        print("x"*50)

if __name__ == "__main__":
    main()
