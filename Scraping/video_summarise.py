# Scraping/video_summarize.py
from transformers import pipeline

_summarizer = None

def get_summarizer():
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6"
        )
    return _summarizer

def chunk_text(text, size=600):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]

def summarize_text(text: str) -> dict:
    summarizer = get_summarizer()

    chunks = chunk_text(text)
    section_summaries = []

    for c in chunks:
        out = summarizer(c, max_length=160, min_length=40, do_sample=False)
        section_summaries.append(out[0]["summary_text"])

    combined = " ".join(section_summaries)

    if len(combined.split()) > 400:
        final = summarizer(
            combined, max_length=250, min_length=80, do_sample=False
        )[0]["summary_text"]
    else:
        final = combined

    return {
        "final_summary": final,
        "section_summaries": section_summaries,
        "chunk_count": len(section_summaries),
        "transcription_length": len(text),
        "transcription_preview": text[:500]
    }
