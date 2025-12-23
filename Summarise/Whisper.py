import whisper
import os
import yt_dlp

def transcribe_audio(video_id):
    # Set up yt-dlp options to download only audio
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    # Download audio from YouTube
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Load whisper model and transcribe
    model = whisper.load_model("base")
    result = model.transcribe("temp_audio.mp3", fp16=False)
    
    # Save transcription to file
    with open("transcription.txt", "w") as f:
        f.write(result["text"])
    
    # Clean up temporary audio file
    if os.path.exists("temp_audio.mp3"):
        os.remove("temp_audio.mp3")
    
    return result["text"]
