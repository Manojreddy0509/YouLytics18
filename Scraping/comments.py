# Scraping/comments.py
from Scraping.P1 import get_vid
from Scraping.P2 import get_comments
from Scraping.model import PretrainedSentimentAnalyzer

def analyze_comments_logic(youtube_url: str, api_key: str) -> dict:
    video_id = get_vid(youtube_url)
    comments = get_comments(video_id, api_key)

    analyzer = PretrainedSentimentAnalyzer()
    sentiment_data = analyzer.analyze_all_comments(comments)

    total = len(comments)

    return {
        'video_id': video_id,
        'total_comments': total,
        'positive': {
            'count': len(sentiment_data['positive']),
            'percentage': round((len(sentiment_data['positive']) / total) * 100, 2) if total else 0,
            'comments': sentiment_data['positive']
        },
        'negative': {
            'count': len(sentiment_data['negative']),
            'percentage': round((len(sentiment_data['negative']) / total) * 100, 2) if total else 0,
            'comments': sentiment_data['negative']
        },
        'neutral': {
            'count': len(sentiment_data['neutral']),
            'percentage': round((len(sentiment_data['neutral']) / total) * 100, 2) if total else 0,
            'comments': sentiment_data['neutral']
        }
    }