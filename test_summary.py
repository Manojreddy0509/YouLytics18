import os
from unittest.mock import MagicMock
import sys

# Mock openai if key is missing
if "OPENAI_API_KEY" not in os.environ:
    print("⚠️  OPENAI_API_KEY not found. Mocking OpenAI response for testing.")
    os.environ["OPENAI_API_KEY"] = "mock-key"
    
    # Patch openai
    import openai
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "## Mock Summary\n\n- Point 1\n- Point 2\n- Point 3\n\nThis is a mock summary because no API key was provided."
    mock_client.chat.completions.create.return_value = mock_response
    
    openai.OpenAI = MagicMock(return_value=mock_client)

from Summarise.simple_summary import process_video_summary, get_transcript, extract_video_id

def test_summary():
    # Trying a different video
    url = "https://www.youtube.com/watch?v=M7FIvfx5J10" # The first video on YouTube (Me at the zoo) - re-upload or similar
    print(f"Testing summary for: {url}")
    
    # Verify extraction
    vid = extract_video_id(url)
    print(f"Extracted Video ID: {vid}")
    
    if not vid:
        print("❌ Failed to extract video ID")
        return

    # Try to process
    result = process_video_summary(url)
    
    if "error" in result:
        print(f"❌ Error during full process: {result['error']}")
        
        # If transcript failed, let's manually mock transcript to test PDF generation
        if "transcript" in result['error'] or "retrieve" in result['error']:
            print("⚠️  Transcript fetch failed (likely network/blocking issue). Mocking transcript to test PDF generation...")
            
            # Manually invoke summarize and PDF generation
            from Summarise.simple_summary import summarize, generate_summary_pdf
            
            mock_transcript = "This is a mock transcript. " * 50
            summary = summarize(mock_transcript)
            print(f"Generated Summary (Mock): {summary[:50]}...")
            
            pdf_path = generate_summary_pdf(summary, f"summary_{vid}_mock.pdf")
            print(f"Generated PDF at: {pdf_path}")
            
            if os.path.exists(pdf_path):
                print("✅ PDF generation confirmed.")
            else:
                print("❌ PDF generation failed.")
            
    else:
        print("✅ Success!")
        print(f"Video ID: {result['video_id']}")
        print(f"Summary: {result['summary'][:100]}...")
        print(f"PDF Path: {result['pdf_path']}")
        
        if os.path.exists(result['pdf_path']):
            print(f"✅ PDF file exists at {result['pdf_path']}")
        else:
            print("❌ PDF file NOT found.")

if __name__ == "__main__":
    test_summary()
