
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

def format_time(seconds):
    """Converts seconds to HH:MM:SS format"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
    return f"{int(m):02d}:{int(s):02d}"

def summarize_segments_to_sections(segments, chunk_duration=300):
    """
    Groups segments into time-based chunks (default 5 mins) and summarizes each chunk.
    Returns a formatted markdown string with sections.
    """
    global SUMMARIZER_MODEL
    if SUMMARIZER_MODEL is None:
        init_summarizer()

    if not segments:
        return ""

    grouped_chunks = []
    current_chunk = {"text": "", "start": segments[0]['start'], "end": segments[0]['end']}
    
    for seg in segments:
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        
        # If adding this segment exceeds the chunk duration (and we have some content), start new chunk
        if (end - current_chunk['start'] > chunk_duration) and current_chunk['text']:
            grouped_chunks.append(current_chunk)
            current_chunk = {"text": text, "start": start, "end": end}
        else:
            current_chunk['text'] += " " + text
            current_chunk['end'] = end
            
    # Add last chunk
    if current_chunk['text']:
        grouped_chunks.append(current_chunk)

    final_output = []
    section_list = []
    
    print(f"📝 Summarizing {len(grouped_chunks)} time-based sections...")

    for i, chunk in enumerate(grouped_chunks):
        text = chunk['text'].strip()
        start_str = format_time(chunk['start'])
        end_str = format_time(chunk['end'])
        
        if len(text.split()) < 30:
            # Too short to summarize, just append text
            summary = text
        else:
            try:
                # We reuse the chunking logic inside summarize_text if the section is still too long
                # But here we just want a summary of this section.
                # Let's call the model directly or use summarize_text logic for this block
                summary = summarize_text(text)
            except Exception as e:
                print(f"   ⚠️ Error summarizing section {start_str}-{end_str}: {e}")
                summary = text

        section_header = f"## Time: {start_str} - {end_str}"
        final_output.append(f"{section_header}\n{summary}\n")
        section_list.append(f"Time {start_str} - {end_str}: {summary}")

    return "\n".join(final_output), section_list