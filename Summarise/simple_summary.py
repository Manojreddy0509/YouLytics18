import re
import os
from fpdf import FPDF
from Summarise.whisp import transcribe_video_or_url
from Summarise.summarize import summarize_segments_to_sections, init_summarizer

# 1. EXTRACT VIDEO ID from URL
def extract_video_id(url):
    patterns = [
        r'(?:v=)([a-zA-Z0-9_-]{11})',      # youtube.com/watch?v=
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})', # youtu.be/
        r'(?:embed/)([a-zA-Z0-9_-]{11})',   # youtube.com/embed/
        r'(?:shorts/)([a-zA-Z0-9_-]{11})'   # youtube.com/shorts/
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# 2. PDF GENERATION
def generate_summary_pdf(summary_text, filename="summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Handle basic markdown cleanup for PDF (simple approach)
    
    # Replace markdown headers with uppercase or just print lines
    lines = summary_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
            
        if line.startswith('## '):
            pdf.set_font("Arial", 'B', 14)
            pdf.multi_cell(0, 10, line.replace('## ', ''))
            pdf.set_font("Arial", size=12)
        elif line.startswith('### '):
            pdf.set_font("Arial", 'B', 13)
            pdf.multi_cell(0, 10, line.replace('### ', ''))
            pdf.set_font("Arial", size=12)
        elif line.startswith('- ') or line.startswith('* '):
             # Use simple dash to avoid latin-1 encoding issues with bullets in standard FPDF
             pdf.multi_cell(0, 8, f"  - {line[2:]}")
        else:
            # Clean up potential unicode characters that might break latin-1
            # Or use encode/decode to strip them if necessary, but simple replacement is safer for now
            clean_line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 8, clean_line)
            
    output_path = os.path.join("static", "downloads", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    return output_path

# 3. Wrapper for the full flow
def process_video_summary(url):
    video_id = extract_video_id(url)
    # Use full URL if possible for yt-dlp, or ID if URL is weird, but whisp handles ID.
    # Let's pass the URL if we can, but whisp handles ID fine.
    
    if not video_id:
        # Maybe it's a valid URL without ID (like some short links), let's try passing URL directly to whisp
        # But for PDF filename we need an ID or name.
        video_id = "video_" + str(hash(url))
        
    print(f"🎬 Processing summary for: {url}")
    
    try:
        # 1. Transcribe (Download + Whisper + Translate)
        # We pass the full URL to ensure yt-dlp gets it right
        text, segments = transcribe_video_or_url(url)
        
        if not text:
             return {"error": "Transcription failed or produced empty text."}

        # 2. Summarize (DistilBART section-wise)
        # Initialize model if not already (it does check internally but good to be sure)
        init_summarizer()
        
        summary, section_list = summarize_segments_to_sections(segments)
        
        if not summary:
            summary = "Summary generation returned empty result."

        # 3. Generate PDF
        pdf_filename = f"summary_{video_id}.pdf"
        pdf_path = generate_summary_pdf(summary, pdf_filename)
        
        return {
            "video_id": video_id,
            "transcript_preview": text[:500] + "...",
            "summary": summary,
            "section_summaries": section_list,
            "pdf_path": pdf_path
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Processing failed: {str(e)}"}
