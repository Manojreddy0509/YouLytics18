# summarize.py - FIXED VERSION
from transformers import pipeline
import os
import traceback

TRANSCRIPTION_FILE = "transcription.txt"
SUMMARY_FILE = "summary.txt"

def chunk_text_by_words(text: str, chunk_size_words: int = 600):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size_words):
        chunks.append(" ".join(words[i:i+chunk_size_words]))
    return chunks

def get_summarizer(model_name: str = "sshleifer/distilbart-cnn-12-6"):
    """
    Try to load a reasonably small summarization model first; fallback to default pipeline model
    if that fails.
    """
    try:
        print(f"🔄 Loading summarization model: {model_name}")
        summarizer = pipeline("summarization", model=model_name)
        print("✅ Summarization model loaded successfully")
        return summarizer
    except Exception as e:
        print(f"❌ Failed to load model {model_name}: {e}")
        try:
            print("🔄 Trying default summarization model...")
            summarizer = pipeline("summarization")
            print("✅ Default summarization model loaded successfully")
            return summarizer
        except Exception as e2:
            print(f"❌ Failed to load default summarization model: {e2}")
            return None

def summarize_text(text: str, summarizer=None, max_length=180, min_length=40):
    """
    Summarize a single text chunk safely (returns string).
    """
    if not text or not text.strip():
        return ""
    
    if summarizer is None:
        summarizer = get_summarizer()
    
    if summarizer is None:
        # Fallback if no summarizer available
        words = text.split()
        if len(words) > 100:
            return " ".join(words[:100]) + "..."
        return text
    
    try:
        print(f"📝 Summarizing text chunk ({len(text)} characters)...")
        out = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        summary = out[0].get("summary_text", "").strip()
        print(f"✅ Chunk summarized to {len(summary)} characters")
        return summary
    except Exception as e:
        print(f"❌ Error summarizing text chunk: {e}")
        # In case model fails on this chunk, return a truncated version as fallback
        words = text.split()
        if len(words) > 100:
            return " ".join(words[:100]) + "... [Summary failed]"
        return text + " [Summary failed]"

def summarize_transcription_file(transcription_path: str = TRANSCRIPTION_FILE, out_path: str = SUMMARY_FILE):
    try:
        print(f"📖 Reading transcription from: {transcription_path}")
        if not os.path.exists(transcription_path):
            raise FileNotFoundError(f"{transcription_path} not found. Run transcription first.")

        with open(transcription_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        if not text:
            raise ValueError("Transcription file is empty; nothing to summarize.")

        print(f"📄 Transcription length: {len(text)} characters")

        # Create summarizer pipeline
        summarizer = get_summarizer()

        # Break into chunks that are safe for summarizer
        chunks = chunk_text_by_words(text, chunk_size_words=600)
        print(f"🔪 Split into {len(chunks)} chunks for processing")

        section_summaries = []
        for idx, chunk in enumerate(chunks, start=1):
            print(f"🔄 Processing chunk {idx}/{len(chunks)}...")
            s = summarize_text(chunk, summarizer=summarizer, max_length=160, min_length=40)
            section_summaries.append(s)
            print(f"✅ Chunk {idx} completed")

        # Combine section summaries into a single text and summarize again to produce a cohesive overall summary
        combined = "\n\n".join([f"Section {i+1}: {summary}" for i, summary in enumerate(section_summaries)])
        
        # If combined is short enough, take it directly; else summarize again
        final_summary = combined
        if len(combined.split()) > 400:
            print("🔄 Creating final summary from combined sections...")
            final_summary = summarize_text(combined, summarizer=summarizer, max_length=250, min_length=80)
        else:
            final_summary = "Overall: " + " ".join([s[:100] for s in section_summaries]) + "..."

        # Save results
        print(f"💾 Saving summary to: {out_path}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("=== SECTION SUMMARIES ===\n\n")
            for i, sec in enumerate(section_summaries, 1):
                f.write(f"Section {i} summary:\n{sec}\n\n")
            f.write("\n=== FINAL SUMMARY ===\n\n")
            f.write(final_summary)

        print("✅ Summarization completed successfully!")
        return {
            "sections": [f"Section {i}: {sec}" for i, sec in enumerate(section_summaries, 1)],
            "final_summary": final_summary
        }

    except Exception as e:
        print(f"❌ Error in summarize_transcription_file: {e}")
        print(f"Debug info: {traceback.format_exc()}")
        
        # Create a basic fallback summary
        fallback_sections = [
            "Section 1: Content overview",
            "Section 2: Key points discussed", 
            "Section 3: Main conclusions"
        ]
        fallback_final = "This is a fallback summary. The automatic summarization encountered an error."
        
        # Still try to write something to the file
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("=== SECTION SUMMARIES ===\n\n")
                for sec in fallback_sections:
                    f.write(f"{sec}\n\n")
                f.write("\n=== FINAL SUMMARY ===\n\n")
                f.write(fallback_final)
        except:
            pass
            
        return {
            "sections": fallback_sections,
            "final_summary": fallback_final
        }