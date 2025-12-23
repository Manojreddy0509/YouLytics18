# debug_imports.py
import sys
import os

print("=== DEBUGGING IMPORTS ===")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Check if Scraping folder exists
scraping_path = os.path.join(os.getcwd(), 'Scraping')
print(f"Scraping folder path: {scraping_path}")
print(f"Scraping folder exists: {os.path.exists(scraping_path)}")

if os.path.exists(scraping_path):
    print(f"Files in Scraping folder: {os.listdir(scraping_path)}")
    
    # Try to import directly from the Scraping folder
    sys.path.insert(0, scraping_path)
    print(f"Added to path: {scraping_path}")
    
    try:
        from P1 import get_vid
        print("✅ SUCCESS: Imported get_vid from P1")
    except ImportError as e:
        print(f"❌ FAILED: {e}")
        
    try:
        from P2 import get_comments
        print("✅ SUCCESS: Imported get_comments from P2")
    except ImportError as e:
        print(f"❌ FAILED: {e}")
        
    try:
        from model import PretrainedSentimentAnalyzer
        print("✅ SUCCESS: Imported PretrainedSentimentAnalyzer from model")
    except ImportError as e:
        print(f"❌ FAILED: {e}")
else:
    print("❌ Scraping folder not found!")