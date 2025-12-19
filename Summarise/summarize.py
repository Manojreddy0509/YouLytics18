
from transformers import pipeline
import traceback

# Global variable for the Summarization model
SUMMARIZER_MODEL = None

def init_summarizer(model_name="sshleifer/distilbart-cnn-12-6"):
    """
    Loads the summarization model into the global variable SUMMARIZER_MODEL.
    Should be called once at worker startup.
    """
    global SUMMARIZER_MODEL
    if SUMMARIZER_MODEL is None:
        print(f"🔄 Loading summarization model: {model_name}...")
        try:
            SUMMARIZER_MODEL = pipeline("summarization", model=model_name)
            print("✅ Summarization model loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load model {model_name}: {e}")
            # Fallback
            try:
                SUMMARIZER_MODEL = pipeline("summarization")
                print("✅ Default summarization model loaded (fallback).")
            except Exception as e2:
                 print(f"❌ Critical: Failed to load any summarization model: {e2}")
                 raise

def chunk_text(text, chunk_size=600):
    """
    Splits text into chunks of roughly chunk_size words.
    """
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

def summarize_text(text):
    """
    Summarizes the text by chunking it, summarizing chunks, and joining them.
    Assumes init_summarizer() has been called.
    """
    global SUMMARIZER_MODEL
    if SUMMARIZER_MODEL is None:
        init_summarizer()

    if not text or len(text.strip()) < 50:
        return text

    print(f"📝 Summarizing text length: {len(text)}")
    chunks = list(chunk_text(text))
    summaries = []

    for i, chunk in enumerate(chunks):
        try:
            # Adjust max_length dynamically based on chunk length
            input_len = len(chunk.split())
            max_len = min(150, max(50, input_len // 2))
            min_len = min(30, max_len // 2)

            res = SUMMARIZER_MODEL(chunk, max_length=max_len, min_length=min_len, do_sample=False)
            summary = res[0]['summary_text'].strip()
            summaries.append(summary)
            print(f"   - Chunk {i+1}/{len(chunks)} summarized.")
        except Exception as e:
            print(f"   ⚠️ Error summarizing chunk {i+1}: {e}")
            summaries.append(chunk[:200] + "...") # Fallback

    final_summary = " ".join(summaries)
    return final_summary