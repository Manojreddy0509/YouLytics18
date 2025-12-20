import sys
import os

# Add the current directory to sys.path so we can import Scraping
sys.path.append(os.getcwd())

from Scraping.transcribe import transcribe_audio_from_video, init_whisper

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
        # Initialize whisper once
        print("📥 Initializing Whisper...")
        init_whisper("base")
        
        # Run transcription
        print("🎬 Running transcribe_audio_from_video...")
        transcript = transcribe_audio_from_video(video_url, video_id)
        
        print("\n" + "="*50)
        print("✅ SUCCESS!")
        print(f"Length: {len(transcript)} characters")
        print("Preview:")
        print(transcript[:500] + "...")
        print("="*50)
        
    except Exception as e:
        print("\n" + "!"*50)
        print("❌ FAILURE!")
        print(f"Error: {e}")
        print("!"*50)
        sys.exit(1)

if __name__ == "__main__":
    main()
