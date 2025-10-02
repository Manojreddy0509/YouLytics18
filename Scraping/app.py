# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add the scraping folder to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Scraping'))

app = Flask(__name__)
CORS(app)

# Now import your modules
try:
    from P1 import get_vid
    from P2 import get_comments
    from model import PretrainedSentimentAnalyzer
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure P1.py, P2.py, and model.py are in the scraping folder")

@app.route('/')
def home():
    return jsonify({"message": "YouTube Sentiment Analyzer API is running!"})

@app.route('/analyze', methods=['POST'])
def analyze_comments():
    try:
        data = request.get_json()
        youtube_url = data.get('url')
        api_key = "AIzaSyDGcHWGFK2BHWswtYvJiMvjmZPuFvxvQ7E"
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        print(f"Analyzing comments for URL: {youtube_url}")
        
        # Get video ID and comments
        video_id = get_vid(youtube_url)
        comments = get_comments(video_id, api_key)
        
        # Analyze sentiment
        analyzer = PretrainedSentimentAnalyzer()
        sentiment_data = analyzer.analyze_all_comments(comments)
        
        # Calculate percentages
        total_comments = len(comments)
        positive_count = len(sentiment_data['positive'])
        negative_count = len(sentiment_data['negative'])
        neutral_count = len(sentiment_data['neutral'])
        
        # Prepare response
        response = {
            'total_comments': total_comments,
            'positive': {
                'count': positive_count,
                'percentage': round((positive_count / total_comments) * 100, 2) if total_comments > 0 else 0,
                'comments': sentiment_data['positive']
            },
            'negative': {
                'count': negative_count,
                'percentage': round((negative_count / total_comments) * 100, 2) if total_comments > 0 else 0,
                'comments': sentiment_data['negative']
            },
            'neutral': {
                'count': neutral_count,
                'percentage': round((neutral_count / total_comments) * 100, 2) if total_comments > 0 else 0,
                'comments': sentiment_data['neutral']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting YouTube Sentiment Analyzer API...")
    app.run(debug=True, port=5000)