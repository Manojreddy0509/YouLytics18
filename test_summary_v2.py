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
    # Trying the video the user likely had issues with or a generic one
    # Let's try a video known to have ONLY auto-generated captions to test that logic
    # or just a standard one.
    # "Me at the zoo" often has weird caption availability.
    # Let's try a popular tech video that definitely has captions.
    # "Python in 100 Seconds" by Fireship: https://www.youtube.com/watch?v=x7X9w_GIm1s
    url = "https://www.youtube.com/watch?v=x7X9w_GIm1s" 
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
    else:
        print("✅ Success!")
        print(f"Video ID: {result['video_id']}")
        print(f"Transcript Length: {len(result.get('transcript_preview', ''))}")
        print(f"Summary: {result['summary'][:100]}...")
        print(f"PDF Path: {result['pdf_path']}")
        
        if os.path.exists(result['pdf_path']):
            print(f"✅ PDF file exists at {result['pdf_path']}")
        else:
            print("❌ PDF file NOT found.")

if __name__ == "__main__":
    test_summary()
