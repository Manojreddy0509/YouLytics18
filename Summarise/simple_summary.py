import re
import os
from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF
import openai

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

# 2. GET TRANSCRIPT using youtube-transcript-api library
def get_transcript(video_id):
    try:
        # List of languages to try, prioritizing English
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB', 'hi', 'es'])
        full_text = ' '.join([entry['text'] for entry in transcript_list])
        return full_text
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

# 3. SUMMARIZE using OpenAI
def summarize(transcript):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY not found in environment variables."
        
    client = openai.OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Using a cost-effective model, can be changed to gpt-4
            messages=[
                {"role": "system", "content": "Summarize this video transcript concisely with key points. Use Markdown formatting (## for sections, - for bullets)."},
                {"role": "user", "content": transcript[:15000]}  # Limit tokens
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during summarization: {e}"

# 4. PDF GENERATION
def generate_summary_pdf(summary_text, filename="summary.pdf"):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Handle basic markdown cleanup for PDF (simple approach)
    # FPDF doesn't support Markdown natively without extensions, 
    # so we'll do some basic cleanup or just print as text.
    # Ideally use a library that supports markdown to PDF, but keeping it simple.
    
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
            
    # Save to buffer or file
    # For web response, we might want to return the path or bytes.
    # Here we save to file.
    output_path = os.path.join("static", "downloads", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    return output_path

# Wrapper for the full flow
def process_video_summary(url):
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}
        
    transcript = get_transcript(video_id)
    if not transcript:
        return {"error": "Could not retrieve transcript. Video might not have captions or they are disabled."}
        
    summary = summarize(transcript)
    
    # Generate PDF
    pdf_filename = f"summary_{video_id}.pdf"
    pdf_path = generate_summary_pdf(summary, pdf_filename)
    
    return {
        "video_id": video_id,
        "transcript_preview": transcript[:500] + "...",
        "summary": summary,
        "pdf_path": pdf_path
    }