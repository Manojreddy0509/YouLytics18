# Scraping/whisper_transcribe.py
import os
import yt_dlp
import whisper

TEMP_AUDIO = "temp_audio.mp3"
_model = None

def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model

def transcribe_youtube(url: str) -> str:
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "temp_audio.%(ext)s",
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        model = get_model()
        result = model.transcribe(TEMP_AUDIO, task="translate", fp16=False)

        if os.path.exists(TEMP_AUDIO):
            os.remove(TEMP_AUDIO)

        return result["text"].strip()
    except (yt_dlp.utils.DownloadError, yt_dlp.networking.exceptions.TransportError, ConnectionError, OSError) as e:
        print(f"❌ Transcription failed due to network/DNS error: {e}")
        return "ERROR: Transcription unavailable due to network restrictions. Please try again later or use a different video."
    except Exception as e:
        print(f"❌ Unexpected transcription error: {e}")
        return "ERROR: Transcription failed unexpectedly. Please try again later."
