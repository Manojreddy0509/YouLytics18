import os
from celery import Celery
from celery.signals import worker_process_init
from Summarise.simple_summary import process_video_summary
from Summarise.summarize import init_summarizer

# Redis Configuration
BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
BACKEND_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

celery = Celery('tasks', broker=BROKER_URL, backend=BACKEND_URL)

# Global analyzer for worker
analyzer = None

@worker_process_init.connect
def init_worker(**kwargs):
    """
    Load models once when the worker process starts.
    """
    print("👷 Worker process initializing...")
    
    # Ensure current directory is in sys.path for module discovery
    import sys
    import os
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())
    
    try:
        # Load Summarization model
        init_summarizer()
        
        # Load Sentiment Analyzer
        global analyzer
        from Scraping.model import PretrainedSentimentAnalyzer
        analyzer = PretrainedSentimentAnalyzer()
        
        print("✅ Models initialized in worker process.")
    except Exception as e:
        print(f"❌ Failed to initialize models in worker: {e}")

@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def transcribe_and_summarize(self, video_url):
    """
    Background task for video summarization.
    """
    print(f"🚀 Summarization Task started for: {video_url}")
    try:
        result = process_video_summary(video_url)
        
        if "error" in result:
             # If it's a hard error, maybe don't retry? But for now we treat as exception
             raise Exception(result["error"])
             
        return result
        
    except Exception as exc:
        print(f"❌ Summarization Task failed: {exc}")
        raise self.retry(exc=exc)

@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def perform_full_analysis(self, video_url, youtube_api_key):
    """
    Background task for full analysis (Comments + Summary).
    """
    print(f"🚀 Full Analysis Task started for: {video_url}")
    try:
        # 1. Comment Analysis
        comments_data = {}
        try:
            from Scraping.P1 import get_vid
            from Scraping.P2 import get_comments
            
            video_id = get_vid(video_url)
            comments = get_comments(video_id, youtube_api_key)
            
            global analyzer
            if analyzer is None:
                from Scraping.model import PretrainedSentimentAnalyzer
                analyzer = PretrainedSentimentAnalyzer()
                
            sentiment_data = analyzer.analyze_all_comments(comments)
            
            total = len(comments)
            comments_data = {
                'video_id': video_id,
                'total_comments': total,
                'positive': {
                    'count': len(sentiment_data['positive']),
                    'percentage': round((len(sentiment_data['positive']) / total) * 100, 2) if total > 0 else 0,
                    'comments': sentiment_data['positive']
                },
                'negative': {
                    'count': len(sentiment_data['negative']),
                    'percentage': round((len(sentiment_data['negative']) / total) * 100, 2) if total > 0 else 0,
                    'comments': sentiment_data['negative']
                },
                'neutral': {
                    'count': len(sentiment_data['neutral']),
                    'percentage': round((len(sentiment_data['neutral']) / total) * 100, 2) if total > 0 else 0,
                    'comments': sentiment_data['neutral']
                }
            }
        except Exception as e:
            print(f"⚠️ Comment analysis part failed: {e}")
            comments_data = {'error': f'Comment analysis failed: {str(e)}'}

        # 2. Summarization
        summary_data = {}
        try:
            summary_result = process_video_summary(video_url)
            if "error" in summary_result:
                summary_data = {'error': summary_result["error"]}
            else:
                summary_data = {
                    'success': True,
                    'transcription_length': len(summary_result.get("transcript_preview", "")),
                    'transcription_preview': summary_result.get("transcript_preview", ""),
                    'final_summary': summary_result.get("summary", ""),
                    'section_summaries': summary_result.get("section_summaries", []),
                    'full_summary': summary_result.get("summary", ""),
                    'pdf_url': f"/static/downloads/{os.path.basename(summary_result['pdf_path'])}"
                }
        except Exception as e:
            print(f"⚠️ Summarization part failed: {e}")
            summary_data = {'error': f'Summarization failed: {str(e)}'}
            
        return {
            'type': 'full',
            'comments_analysis': comments_data,
            'video_summary': summary_data
        }

    except Exception as exc:
        print(f"❌ Full Analysis Task failed: {exc}")
        raise self.retry(exc=exc)

@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def analyze_comments_task(self, video_url, youtube_api_key):
    """
    Background task for comment analysis.
    """
    print(f"🚀 Comment Analysis Task started for: {video_url}")
    try:
        from Scraping.P1 import get_vid
        from Scraping.P2 import get_comments
        
        video_id = get_vid(video_url)
        comments = get_comments(video_id, youtube_api_key)
        
        global analyzer
        if analyzer is None:
            from Scraping.model import PretrainedSentimentAnalyzer
            analyzer = PretrainedSentimentAnalyzer()
            
        sentiment_data = analyzer.analyze_all_comments(comments)
        
        total = len(comments)
        result = {
            'type': 'comments', 
            'video_id': video_id,
            'total_comments': total,
            'positive': {
                'count': len(sentiment_data['positive']),
                'percentage': round((len(sentiment_data['positive']) / total) * 100, 2) if total > 0 else 0,
                'comments': sentiment_data['positive']
            },
            'negative': {
                'count': len(sentiment_data['negative']),
                'percentage': round((len(sentiment_data['negative']) / total) * 100, 2) if total > 0 else 0,
                'comments': sentiment_data['negative']
            },
            'neutral': {
                'count': len(sentiment_data['neutral']),
                'percentage': round((len(sentiment_data['neutral']) / total) * 100, 2) if total > 0 else 0,
                'comments': sentiment_data['neutral']
            }
        }
        return result
        
    except Exception as exc:
        print(f"❌ Comment Analysis Task failed: {exc}")
        raise self.retry(exc=exc)
