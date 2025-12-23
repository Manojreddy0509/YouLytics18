# main.py
import sys
from transcribe import transcribe_video_or_url, TRANSCRIPTION_FILE
from summarize import summarize_transcription_file, SUMMARY_FILE

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <youtube-url-or-id-or-local-video-file>")
        sys.exit(1)

    source = sys.argv[1]
    print("Starting transcription (this may take some minutes depending on model size and hardware)...")
    text = transcribe_video_or_url(source)
    print(f"Transcription saved to {TRANSCRIPTION_FILE} (first 300 chars):\n")
    print(text[:300] + ("..." if len(text) > 300 else ""))
    print("\nNow summarizing...")
    out = summarize_transcription_file(TRANSCRIPTION_FILE, SUMMARY_FILE)
    print(f"\nSummary written to {SUMMARY_FILE}. Final summary (first 1000 chars):\n")
    print(out['final_summary'][:1000])

if __name__ == "__main__":
    main()
