# Example usage
# pip install requests
from P1 import get_vid
from P2 import get_comments
from P3 import save_comments
from model import PretrainedSentimentAnalyzer  # <-- This is required

api_key = "AIzaSyDGcHWGFK2BHWswtYvJiMvjmZPuFvxvQ7E"
url = "https://www.youtube.com/watch?v=8xUher8-5_Q"
video_id = get_vid(url)
comments = get_comments(video_id, api_key)
save_comments(comments, "comments.txt")

# Classify comments using the ensemble model
analyzer = PretrainedSentimentAnalyzer()
sentiment_data = analyzer.analyze_all_comments(comments)

# Print summary
print("Total comments fetched:", len(comments))
print("Positive comments:", len(sentiment_data['positive']))
print("Negative comments:", len(sentiment_data['negative']))
print("Neutral comments:", len(sentiment_data['neutral']))

print("\n=== Positive Comments ===")
for item in sentiment_data['positive']:
    print(item['comment'])

print("\n=== Negative Comments ===")
for item in sentiment_data['negative']:
    print(item['comment'])

print("\n=== Neutral Comments ===")
for item in sentiment_data['neutral']:
    print(item['comment'])

# Optionally, save classified comments to JSON
import json
with open("classified_comments.json", "w", encoding="utf-8") as f:
    json.dump(sentiment_data, f, ensure_ascii=False, indent=2)