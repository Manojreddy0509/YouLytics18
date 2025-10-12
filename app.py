import warnings
import logging

# Suppress Python warnings
warnings.filterwarnings("ignore")
# Suppress Transformers library info/warnings
logging.getLogger("transformers").setLevel(logging.ERROR)

# Suppress Flask/Werkzeug info logs (only show errors)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

os.environ["TOKENIZERS_PARALLELISM"] = "false"
import uuid
import traceback
import sqlite3
import bcrypt
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
JWT_SECRET = os.getenv('JWT_SECRET', 'fallback-jwt-secret')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
CORS(app)

# Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Authentication routes
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Save to database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
            conn.commit()
            
            # Generate JWT token
            token = jwt.encode({
                'user_id': c.lastrowid,
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, JWT_SECRET, algorithm='HS256')

            return jsonify({
                'message': 'User created successfully',
                'token': token,
                'user': {'email': email}
            }), 201

        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already exists'}), 400
        finally:
            conn.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Get user from database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT id, email, password FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            # Generate JWT token
            token = jwt.encode({
                'user_id': user[0],
                'email': user[1],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, JWT_SECRET, algorithm='HS256')

            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {'email': user[1]}
            })
        else:
            return jsonify({'error': 'Invalid email or password'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# JWT token required decorator
def token_required(f):
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user = data
        except:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    
    decorator.__name__ = f.__name__
    return decorator

# Import comment analysis
try:
    from Scraping.P1 import get_vid
    from Scraping.P2 import get_comments
    from Scraping.model import PretrainedSentimentAnalyzer
    analyzer = PretrainedSentimentAnalyzer()
    COMMENT_AVAILABLE = True
    print("✅ Comment analysis modules loaded successfully")
except Exception as e:
    COMMENT_AVAILABLE = False
    print(f"❌ Comment analysis import failed: {e}")

# Import summarization
try:
    from Scraping.transcribe import transcribe_video_or_url
    from Summarise.summarize import summarize_transcription_file
    SUMMARIZE_AVAILABLE = True
    print("✅ Summarization modules loaded successfully")
except Exception as e:
    SUMMARIZE_AVAILABLE = False
    print(f"❌ Summarization import failed: {e}")

@app.route('/')
def home():
    return jsonify({
        "message": "YouLytics API is running!",
        "status": {
            "comment_analysis": COMMENT_AVAILABLE,
            "video_summarization": SUMMARIZE_AVAILABLE
        },
        "endpoints": {
            "/register": "POST - Create new account",
            "/login": "POST - Login to account",
            "/analyze-comments": "POST - Analyze comment sentiment",
            "/summarize-video": "POST - Summarize video content", 
            "/full-analysis": "POST - Complete analysis (comments + summary)"
        }
    })

@app.route('/analyze-comments', methods=['POST'])
@token_required
def analyze_comments():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        youtube_url = data.get('url')
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        if not COMMENT_AVAILABLE:
            return jsonify({'error': 'Comment analysis not available'}), 500
            
        print(f"🔍 Analyzing comments for: {youtube_url}")
        video_id = get_vid(youtube_url)
        comments = get_comments(video_id, YOUTUBE_API_KEY)  # Use env variable
        sentiment_data = analyzer.analyze_all_comments(comments)
        
        total = len(comments)
        response = {
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
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in analyze-comments: {str(e)}")
        return jsonify({'error': f'Comment analysis failed: {str(e)}'}), 500

@app.route('/summarize-video', methods=['POST'])
@token_required
def summarize_video():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        youtube_url = data.get('url')
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        if not SUMMARIZE_AVAILABLE:
            return jsonify({'error': 'Video summarization is not available'}), 500
            
        print(f"🎥 Summarizing video for: {youtube_url}")
        request_id = str(uuid.uuid4())[:8]
        transcription_file = f"transcription_{request_id}.txt"
        summary_file = f"summary_{request_id}.txt"
        
        transcription = transcribe_video_or_url(youtube_url)
        
        with open(transcription_file, 'w', encoding='utf-8') as f:
            f.write(transcription)
        
        summary_result = summarize_transcription_file(transcription_file, summary_file)
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            full_summary = f.read()
        
        # Cleanup
        for file in [transcription_file, summary_file]:
            if os.path.exists(file):
                os.remove(file)
        
        return jsonify({
            'type': 'summary',
            'success': True,
            'transcription_length': len(transcription),
            'transcription_preview': transcription[:500] + "..." if len(transcription) > 500 else transcription,
            'full_summary': full_summary,
            'section_summaries': summary_result.get('sections', []),
            'final_summary': summary_result.get('final_summary', '')
        })
        
    except Exception as e:
        print(f"❌ Error in summarize-video: {str(e)}")
        return jsonify({'error': f'Video summarization failed: {str(e)}'}), 500

@app.route('/full-analysis', methods=['POST'])
@token_required
def full_analysis():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        youtube_url = data.get('url')
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        print(f"🎯 Starting full analysis for: {youtube_url}")
        
        # Comments analysis
        comments_data = {}
        if COMMENT_AVAILABLE:
            video_id = get_vid(youtube_url)
            comments = get_comments(video_id, YOUTUBE_API_KEY)  # Use env variable
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
        else:
            comments_data = {'error': 'Comment analysis not available'}
        
        # Video summarization
        summary_data = {}
        if SUMMARIZE_AVAILABLE:
            try:
                request_id = str(uuid.uuid4())[:8]
                transcription_file = f"transcription_{request_id}.txt"
                summary_file = f"summary_{request_id}.txt"
                
                transcription = transcribe_video_or_url(youtube_url)
                
                with open(transcription_file, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                
                summary_result = summarize_transcription_file(transcription_file, summary_file)
                
                with open(summary_file, 'r', encoding='utf-8') as f:
                    full_summary = f.read()
                
                # Cleanup
                for file in [transcription_file, summary_file]:
                    if os.path.exists(file):
                        os.remove(file)
                
                summary_data = {
                    'success': True,
                    'transcription_length': len(transcription),
                    'transcription_preview': transcription[:500] + "..." if len(transcription) > 500 else transcription,
                    'full_summary': full_summary,
                    'section_summaries': summary_result.get('sections', []),
                    'final_summary': summary_result.get('final_summary', '')
                }
            except Exception as e:
                summary_data = {'error': f'Summarization failed: {str(e)}'}
        else:
            summary_data = {'error': 'Video summarization not available'}
        
        return jsonify({
            'type': 'full', 
            'comments_analysis': comments_data,
            'video_summary': summary_data
        })
        
    except Exception as e:
        print(f"❌ Error in full-analysis: {str(e)}")
        return jsonify({'error': f'Full analysis failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 YouLytics API Starting...")
    print(f"   Comment Analysis: {'✅' if COMMENT_AVAILABLE else '❌'}")
    print(f"   Video Summarization: {'✅' if SUMMARIZE_AVAILABLE else '❌'}")
    print("   Authentication: ✅ Built-in")
    print("   Environment: ✅ Loaded")
    print("   Server: http://127.0.0.1:5001")
    print("=" * 50)
    app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1')
